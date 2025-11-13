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
import signal
import subprocess
from pathlib import Path
from typing import Optional


class IntegrationTestRunner:
    """Manages running integration tests against a remote ChatrixCD instance."""

    def __init__(self, config_path: str):
        """Initialize with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.bot_process: Optional[subprocess.Popen] = None

    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _get_remote_config(self) -> dict:
        """Read and parse the config.json from the remote server."""
        print("Reading configuration from remote server...")
        
        # Read the config file from remote server
        cat_cmd = f"su {self.config['chatrix_user']} -c 'cat {self.config['chatrix_dir']}/config.json'"
        config_json = self._run_ssh_command(cat_cmd)
        
        try:
            remote_config = json.loads(config_json)
            return remote_config
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse remote config.json: {e}") from None

    def _extract_matrix_config(self, remote_config: dict) -> dict:
        """Extract Matrix configuration from remote config."""
        matrix_config = {}
        
        # Extract homeserver
        if 'matrix' in remote_config and 'homeserver' in remote_config['matrix']:
            matrix_config['homeserver'] = remote_config['matrix']['homeserver']
        else:
            raise RuntimeError("Matrix homeserver not found in remote config")
        
        # Extract bot user ID
        if 'matrix' in remote_config and 'user_id' in remote_config['matrix']:
            matrix_config['bot_user_id'] = remote_config['matrix']['user_id']
        else:
            raise RuntimeError("Bot user_id not found in remote config")
        
        # Extract allowed rooms (use first one as test room)
        if 'allowed_rooms' in remote_config and remote_config['allowed_rooms']:
            matrix_config['room_id'] = remote_config['allowed_rooms'][0]
        else:
            raise RuntimeError("No allowed_rooms found in remote config")
        
        return matrix_config

    def start_bot(self) -> None:
        """Start ChatrixCD on the remote machine."""
        print("Updating ChatrixCD on remote machine...")
        
        # Update code and dependencies
        update_cmd = f"su {self.config['chatrix_user']} -c 'cd {self.config['chatrix_dir']} && git pull && uv pip install -r requirements.txt && uv pip install -e .'"
        self._run_ssh_command(update_cmd)
        print("Code updated and dependencies installed")
        
        print("Starting ChatrixCD on remote machine...")
        
        # Switch to chatrix user and start the bot
        start_cmd = f"su {self.config['chatrix_user']} -c 'cd {self.config['chatrix_dir']} && {self.config['venv_activate']} && nohup {self.config['chatrix_command']} > chatrix.log 2>&1 & echo $!'"
        
        # Get the PID
        pid_output = self._run_ssh_command(start_cmd)
        try:
            self.bot_pid = int(pid_output)
            print(f"ChatrixCD started with PID: {self.bot_pid}")
        except ValueError:
            raise RuntimeError(f"Failed to get PID from output: {pid_output}") from None
        
        # Wait a bit for the bot to start
        time.sleep(5)
        
        # Verify it's running
        check_cmd = f"ps -p {self.bot_pid} -o pid,cmd | grep chatrix"
        try:
            self._run_ssh_command(check_cmd, self.config['chatrix_user'])
            print("ChatrixCD is running")
        except RuntimeError:
            raise RuntimeError("Failed to verify ChatrixCD is running") from None

    def stop_bot(self) -> None:
        """Stop ChatrixCD on the remote machine."""
        if self.bot_pid:
            print(f"Stopping ChatrixCD (PID: {self.bot_pid})...")
            try:
                stop_cmd = f"kill {self.bot_pid}"
                self._run_ssh_command(stop_cmd, self.config['chatrix_user'])
                print("ChatrixCD stopped")
            except RuntimeError as e:
                print(f"Warning: Failed to stop ChatrixCD: {e}")
        else:
            print("No bot PID to stop")

    def run_tests(self) -> bool:
        """Run the integration tests."""
        print("Running integration tests...")

        # Set environment variable for config
        env = os.environ.copy()
        env['INTEGRATION_CONFIG'] = str(self.config_path)

        # Run pytest on the integration test
        test_cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_integration_matrix.py",
            "-v",
            "--tb=short"
        ]

        result = subprocess.run(
            test_cmd,
            cwd=Path(__file__).parent.parent,
            env=env,
            timeout=self.config.get('test_timeout', 300)
        )

        return result.returncode == 0

    def run(self) -> bool:
        """Run the complete integration test cycle."""
        try:
            # Get Matrix configuration from remote server
            remote_config = self._get_remote_config()
            matrix_config = self._extract_matrix_config(remote_config)
            
            # Merge with local config for test environment
            test_config = self.config.copy()
            test_config['matrix'] = matrix_config
            
            # Add test client credentials
            if 'test_client' in self.config:
                test_config['matrix'].update(self.config['test_client'])
            
            # Set environment variable for the test
            os.environ['INTEGRATION_CONFIG'] = json.dumps(test_config)
            
            self.start_bot()
            success = self.run_tests()
            return success
        finally:
            self.stop_bot()


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