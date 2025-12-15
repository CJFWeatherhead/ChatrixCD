#!/usr/bin/env python3
"""Script to run integration tests against a live ChatrixCD instance.

This script:
1. SSH to the remote machine
2. Start ChatrixCD in the background
3. Run the integration tests
4. Stop ChatrixCD
5. Report results
"""

import os
import sys
import json
import time
import subprocess
import hjson
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Manages running integration tests against remote ChatrixCD instances."""

    def __init__(self, config_path: str):
        """Initialize with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.hosts = self.config.get(
            "hosts", [self.config]
        )  # Support both old single host and new multi-host format
        self.current_host = None
        self.bot_pid = None  # Initialize bot_pid
        self.bot_process: Optional[subprocess.Popen] = None

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}"
            )

        with open(self.config_path, "r") as f:
            return json.load(f)

    def _get_remote_config(self) -> dict:
        """Read and parse the config.json from the remote server."""
        print(
            f"Reading configuration from remote server {self.current_host['remote_host']}..."
        )

        # Read the config file from remote server (using root to access chatrix directory)
        cat_cmd = f"cat {self.current_host['chatrix_dir']}/config.json"
        config_json = self._run_ssh_command(cat_cmd)

        print(f"Raw config output (first 200 chars): {config_json[:200]}")

        try:
            remote_config = hjson.loads(config_json)
            return remote_config
        except Exception as e:
            print(f"HJSON parse error: {e}")
            print(f"Full config output: {config_json}")
            raise RuntimeError(
                f"Failed to parse remote config.json: {e}"
            ) from None

    def _extract_matrix_config(self, remote_config: dict) -> dict:
        """Extract Matrix configuration from remote config."""
        matrix_config = {}

        # Extract homeserver
        if (
            "matrix" in remote_config
            and "homeserver" in remote_config["matrix"]
        ):
            matrix_config["homeserver"] = remote_config["matrix"]["homeserver"]
        else:
            raise RuntimeError("Matrix homeserver not found in remote config")

        # Extract bot user ID
        if "matrix" in remote_config and "user_id" in remote_config["matrix"]:
            matrix_config["bot_user_id"] = remote_config["matrix"]["user_id"]
        else:
            raise RuntimeError("Bot user_id not found in remote config")

        # Extract device ID
        if (
            "matrix" in remote_config
            and "device_id" in remote_config["matrix"]
        ):
            matrix_config["device_id"] = remote_config["matrix"]["device_id"]

        # Extract access token from config first (for password auth)
        if (
            "matrix" in remote_config
            and "access_token" in remote_config["matrix"]
        ):
            matrix_config["access_token"] = remote_config["matrix"][
                "access_token"
            ]
        else:
            # For OIDC auth, try to get access token from session file
            try:
                session_data = self._get_session_from_remote()
                if session_data and "access_token" in session_data:
                    matrix_config["access_token"] = session_data[
                        "access_token"
                    ]
                    logger.info(
                        "Retrieved access token from remote session file"
                    )
                else:
                    logger.warning(
                        f"No access token found in session data: {session_data}"
                    )
            except Exception as e:
                logger.warning(
                    f"Could not retrieve access token from session file: {e}"
                )

        # Extract allowed rooms (use first one as test room)
        if (
            "bot" in remote_config
            and "allowed_rooms" in remote_config["bot"]
            and remote_config["bot"]["allowed_rooms"]
        ):
            matrix_config["room_id"] = remote_config["bot"]["allowed_rooms"][0]
        else:
            raise RuntimeError("No allowed_rooms found in remote config")

        # Extract command prefix
        if "bot" in remote_config and "command_prefix" in remote_config["bot"]:
            matrix_config["command_prefix"] = remote_config["bot"][
                "command_prefix"
            ]
        else:
            matrix_config["command_prefix"] = "!cd"  # Default fallback

        return matrix_config

    def _get_session_from_remote(self) -> Optional[dict]:
        """Get session data from the remote machine's store directory."""
        try:
            # Try to read the session file from the remote machine
            session_cmd = "cat /home/chatrix/ChatrixCD/store/session.json"
            session_output = self._run_ssh_command(session_cmd, user="root")

            if session_output.strip():
                logger.info(
                    f"Raw session file content: {session_output.strip()[:200]}..."
                )
                session_data = json.loads(session_output.strip())
                logger.info(
                    f"Parsed session data keys: {list(session_data.keys()) if session_data else 'None'}"
                )
                return session_data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse session JSON: {e}")
        except Exception as e:
            logger.debug(f"Could not read session file from remote: {e}")

        return None

    def _run_ssh_command(
        self,
        command: str,
        user: str = "root",
        max_retries: int = 3,
        timeout: int = 30,
    ) -> str:
        """Run a command on the remote host via SSH with retry logic."""
        ssh_cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-i",
            os.path.expanduser(
                self.config.get("ssh_key_path", "~/.ssh/id_rsa")
            ),
            f"{user}@{self.current_host['remote_host']}",
            command,
        ]

        last_error = None
        for attempt in range(max_retries):
            try:
                print(
                    f"SSH attempt {attempt + 1}/{max_retries}: {command[:50]}..."
                )
                result = subprocess.run(
                    ssh_cmd, capture_output=True, text=True, timeout=timeout
                )

                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    last_error = RuntimeError(
                        f"SSH command failed: {result.stderr}"
                    )
                    print(
                        f"SSH attempt {attempt + 1} failed: {result.stderr.strip()}"
                    )

            except subprocess.TimeoutExpired:
                last_error = RuntimeError("SSH command timed out")
                print(f"SSH attempt {attempt + 1} timed out")

            if attempt < max_retries - 1:
                print("Retrying in 2 seconds...")
                time.sleep(2)

        raise last_error

    def start_bot(self) -> None:
        """Start ChatrixCD on the remote machine."""
        print(
            f"Updating ChatrixCD on remote machine {self.current_host['remote_host']}..."
        )

        # Update code and dependencies as chatrix user
        # Use uv with explicit Python path to install into the venv
        chatrix_dir = self.current_host['chatrix_dir']
        chatrix_user = self.current_host['chatrix_user']
        update_cmd = (
            f"su - {chatrix_user} -c "
            f"'cd {chatrix_dir} && git pull && "
            f"uv venv .venv && "
            f"uv pip install --python .venv/bin/python -r requirements.txt && "
            f"uv pip install --python .venv/bin/python -e .'"
        )
        self._run_ssh_command(
            update_cmd, timeout=180
        )  # Give it 3 minutes for wheel downloads
        print("Code updated and dependencies installed")

        print("Starting ChatrixCD on remote machine...")

        # Start the bot as chatrix user
        start_cmd = f"su - {self.current_host['chatrix_user']} -c 'cd {self.current_host['chatrix_dir']} && {self.current_host['venv_activate']} && nohup {self.current_host['chatrix_command']} > chatrix.log 2>&1 & echo $!'"

        # Get the PID
        pid_output = self._run_ssh_command(start_cmd)
        try:
            self.bot_pid = int(pid_output)
            print(f"ChatrixCD started with PID: {self.bot_pid}")
        except ValueError:
            raise RuntimeError(
                f"Failed to get PID from output: {pid_output}"
            ) from None

        # Wait a bit for the bot to start
        time.sleep(5)

        # Verify it's running (use BusyBox compatible ps)
        check_cmd = f"ps | grep {self.bot_pid} | grep chatrix"
        try:
            result = self._run_ssh_command(check_cmd)
            if str(self.bot_pid) in result and "chatrix" in result:
                print("ChatrixCD is running")
            else:
                raise RuntimeError("ChatrixCD process not found")
        except RuntimeError:
            raise RuntimeError(
                "Failed to verify ChatrixCD is running"
            ) from None

    def copy_store_from_remote(self, host_config: dict) -> str:
        """Copy the store directory from remote machine to local temp directory."""
        import tempfile
        import os

        # Create local temp directory for the store
        local_store_dir = tempfile.mkdtemp(prefix="chatrix_remote_store_")
        print(f"Created local store directory: {local_store_dir}")

        # Remote store path
        remote_store_path = f"{host_config['chatrix_dir']}/store"

        # Check if remote store exists
        check_cmd = f"test -d {remote_store_path} && echo 'exists' || echo 'not exists'"
        exists = self._run_ssh_command(check_cmd, user="root")

        if exists != "exists":
            print(
                f"Remote store directory does not exist: {remote_store_path}"
            )
            return local_store_dir  # Return empty dir

        # Copy the entire store directory using tar over SSH
        print(
            f"Copying store from {host_config['remote_host']}:{remote_store_path} to {local_store_dir}"
        )

        # Use tar to copy directory over SSH
        tar_cmd = f"cd {host_config['chatrix_dir']} && tar czf - store"
        scp_cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-i",
            os.path.expanduser(
                self.config.get("ssh_key_path", "~/.ssh/id_rsa")
            ),
            f"root@{host_config['remote_host']}",
            tar_cmd,
        ]

        try:
            import subprocess

            result = subprocess.run(
                scp_cmd, capture_output=True, cwd=local_store_dir
            )
            if result.returncode == 0:
                # Extract the tar
                extract_cmd = ["tar", "xzf", "-"]
                extract_result = subprocess.run(
                    extract_cmd, input=result.stdout, cwd=local_store_dir
                )
                if extract_result.returncode == 0:
                    print("Store copied successfully")
                else:
                    print(
                        f"Failed to extract store: {extract_result.stderr.decode()}"
                    )
            else:
                print(f"Failed to copy store: {result.stderr.decode()}")
        except Exception as e:
            print(f"Error copying store: {e}")

        return local_store_dir

    def collect_logs_from_remote(self, host_config: dict) -> str:
        """Collect logs from remote machine for analysis."""
        print(f"Collecting logs from {host_config['remote_host']}...")

        # Get the log file
        log_cmd = f"cat {host_config['chatrix_dir']}/chatrix.log"
        try:
            logs = self._run_ssh_command(log_cmd, user="root", timeout=30)
            return logs
        except Exception as e:
            print(f"Failed to collect logs: {e}")
            return ""

    def analyze_logs(self, logs: str, bot_user_id: str) -> None:
        """Analyze logs for errors and redaction effectiveness."""
        lines = logs.split("\n")
        errors = []
        sensitive_patterns = [
            r"access_token.*:",
            r"password.*:",
            r"secret.*:",
            r"key.*:",
            r"token.*:",
            r"auth.*:",
        ]

        for line in lines:
            if "ERROR" in line or "Exception" in line or "Traceback" in line:
                errors.append(line)

            # Check for potential sensitive data leaks (basic check)
            for pattern in sensitive_patterns:
                if pattern.lower() in line.lower() and (
                    "redacted" not in line.lower()
                ):
                    print(
                        f"⚠️  Potential sensitive data in log for {bot_user_id}: {line[:200]}..."
                    )

        if errors:
            print(f"❌ Errors found in logs for {bot_user_id}:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
        else:
            print(f"✅ No errors found in logs for {bot_user_id}")

    def stop_bot(self) -> None:
        """Stop ChatrixCD on the remote machine."""
        if self.bot_pid:
            print(f"Stopping ChatrixCD (PID: {self.bot_pid})...")
            try:
                stop_cmd = f"kill {self.bot_pid}"
                self._run_ssh_command(stop_cmd)
                print("ChatrixCD stopped")
            except RuntimeError as e:
                print(f"Warning: Failed to stop ChatrixCD: {e}")
        else:
            print("No bot PID to stop")

    def run_tests(self) -> bool:
        """Run the integration tests."""
        print("Running integration tests...")

        # Run pytest on the integration test
        test_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_integration_matrix.py",
            "-v",
            "--tb=short",
            "-s",  # Don't capture output
        ]

        result = subprocess.run(
            test_cmd,
            cwd=Path(__file__).parent.parent,
            timeout=self.config.get("test_timeout", 10)
            + 10,  # Add some buffer
        )

        return result.returncode == 0

    def run(self) -> bool:
        """Run the complete integration test cycle with all bots running simultaneously."""
        overall_success = True

        # First, collect all bot configurations
        all_bot_configs = []
        for host_config in self.hosts:
            self.current_host = host_config
            try:
                remote_config = self._get_remote_config()
                matrix_config = self._extract_matrix_config(remote_config)
                all_bot_configs.append(
                    {
                        "host": host_config["remote_host"],
                        "matrix_config": matrix_config,
                        "host_config": host_config,
                    }
                )
            except Exception as e:
                print(
                    f"Failed to get config for host {host_config['remote_host']}: {e}"
                )
                overall_success = False
                continue

        if len(all_bot_configs) < 2:
            print(
                "Warning: Need at least 2 bots for cross-testing. Running basic tests only."
            )

        # Start all bots simultaneously
        running_bots = []
        for bot_config in all_bot_configs:
            self.current_host = bot_config["host_config"]
            try:
                # Copy store before starting bot so it loads the existing store
                store_path = self.copy_store_from_remote(
                    bot_config["host_config"]
                )
                bot_config["store_path"] = store_path

                self.start_bot()
                running_bots.append(bot_config)
                print(
                    f"✅ Started bot {bot_config['matrix_config']['bot_user_id']}"
                )
            except Exception as e:
                print(
                    f"❌ Failed to start bot {bot_config['matrix_config']['bot_user_id']}: {e}"
                )
                overall_success = False

        if not running_bots:
            print("❌ No bots could be started")
            return False

        # Wait for bots to fully start and sync
        print("Waiting 10 seconds for bots to sync...")
        time.sleep(10)

        # Copy stores from all running bots
        print("Copying encryption stores from remote machines...")
        store_paths = {}
        for bot_config in running_bots:
            try:
                store_path = self.copy_store_from_remote(
                    bot_config["host_config"]
                )
                store_paths[bot_config["matrix_config"]["bot_user_id"]] = (
                    store_path
                )
                print(
                    f"✅ Copied store for {bot_config['matrix_config']['bot_user_id']}"
                )
            except Exception as e:
                print(
                    f"❌ Failed to copy store for {bot_config['matrix_config']['bot_user_id']}: {e}"
                )
                store_paths[bot_config["matrix_config"]["bot_user_id"]] = None

        # Now run tests for each running bot
        for i, bot_config in enumerate(running_bots):
            print(f"\n{'='*50}")
            print(
                f"Testing bot {i+1}/{len(running_bots)}: {bot_config['matrix_config']['bot_user_id']} on {bot_config['host']}"
            )
            print(f"{'='*50}")

            try:
                # Prepare test config with information about all bots
                test_config = self.config.copy()
                test_config["matrix"] = bot_config["matrix_config"]
                test_config["all_bots"] = [
                    config["matrix_config"] for config in running_bots
                ]

                # Add test configuration
                test_config["test_room"] = self.config.get("test_room")
                test_config["test_client"] = self.config.get("test_client")
                test_config["test_timeout"] = self.config.get(
                    "test_timeout", 10
                )

                # Add store paths
                test_config["store_paths"] = store_paths

                # Set environment variable for the test
                os.environ["INTEGRATION_CONFIG"] = json.dumps(test_config)

                success = self.run_tests()
                if not success:
                    overall_success = False
                    print(
                        f"❌ Tests failed for bot {bot_config['matrix_config']['bot_user_id']}"
                    )
                else:
                    print(
                        f"✅ Tests passed for bot {bot_config['matrix_config']['bot_user_id']}"
                    )

            except Exception as e:
                print(
                    f"❌ Error testing bot {bot_config['matrix_config']['bot_user_id']}: {e}"
                )
                overall_success = False

        # Stop all bots
        for bot_config in running_bots:
            self.current_host = bot_config["host_config"]
            try:
                self.stop_bot()
                print(
                    f"✅ Stopped bot {bot_config['matrix_config']['bot_user_id']}"
                )
            except Exception as e:
                print(
                    f"Warning: Failed to stop bot {bot_config['matrix_config']['bot_user_id']}: {e}"
                )

        # Collect and analyze logs from all bots
        print("\nCollecting and analyzing logs...")
        for bot_config in running_bots:
            try:
                logs = self.collect_logs_from_remote(bot_config["host_config"])
                self.analyze_logs(
                    logs, bot_config["matrix_config"]["bot_user_id"]
                )
            except Exception as e:
                print(
                    f"Failed to analyze logs for {bot_config['matrix_config']['bot_user_id']}: {e}"
                )

        return overall_success


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python run_integration_tests.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        runner = IntegrationTestRunner(config_path)
        success = runner.run()

        if success:
            print("✅ Integration tests passed!")
            sys.exit(0)
        else:
            print("❌ Integration tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Integration test setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
