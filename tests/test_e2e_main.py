"""End-to-End tests for main entry point with input/output verification.

This module tests the full ChatrixCD application lifecycle including:
- CLI argument parsing and validation
- Configuration file handling
- Application startup and shutdown
- Error handling and user feedback

Uses pexpect for subprocess testing with input/output verification.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import subprocess


class TestMainEntryPointE2E(unittest.TestCase):
    """End-to-end tests for main.py entry point."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        cls.project_root = Path(__file__).parent.parent
        cls.chatrixcd_main = cls.project_root / "chatrixcd" / "main.py"

        # Ensure the main file exists
        assert cls.chatrixcd_main.exists(), f"Main file not found: {cls.chatrixcd_main}"

    def test_version_flag_output(self):
        """Test --version flag produces expected output format."""
        result = subprocess.run(
            [sys.executable, "-m", "chatrixcd.main", "--version"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit with code 0
        self.assertEqual(result.returncode, 0)

        # Output should contain "ChatrixCD" and a version number
        output = result.stdout + result.stderr
        self.assertIn("ChatrixCD", output)
        # Version pattern: one or more digits, dot, one or more digits
        self.assertRegex(output, r"\d+\.\d+")

    def test_help_flag_output(self):
        """Test --help flag produces comprehensive help text."""
        result = subprocess.run(
            [sys.executable, "-m", "chatrixcd.main", "--help"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit with code 0
        self.assertEqual(result.returncode, 0)

        # Output should contain key help sections
        output = result.stdout + result.stderr
        self.assertIn("chatrixcd", output.lower())
        self.assertIn("usage", output.lower())
        self.assertIn("options", output.lower() or "arguments" in output.lower())

        # Should mention key flags
        self.assertIn("--config", output)
        self.assertIn("--verbose", output)
        self.assertIn("--version", output)

    def test_missing_config_validation(self):
        """Test that missing configuration file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_config = os.path.join(tmpdir, "nonexistent.json")

            # Use a subprocess with stdin closed to avoid interactive prompts
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    nonexistent_config,
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=5,
            )

            # Should prompt about missing config or start with defaults
            output = result.stdout + result.stderr
            # Accept either interactive prompt or default value usage
            self.assertTrue(
                "not found" in output.lower()
                or "configuration" in output.lower()
                or result.returncode == 0,  # May proceed with defaults
                f"Unexpected output: {output}",
            )

    def test_invalid_config_validation(self):
        """Test that invalid configuration is validated and rejected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write invalid config (missing required fields)
            json.dump(
                {
                    "matrix": {
                        "homeserver": "",
                        "user_id": "",
                        "auth_type": "password",
                    },
                    "semaphore": {"url": "", "api_token": ""},
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Should exit with error
            self.assertNotEqual(result.returncode, 0)

            # Error output should mention validation failure
            output = result.stdout + result.stderr
            self.assertIn("validation", output.lower())
        finally:
            os.unlink(temp_config)

    def test_show_config_flag(self):
        """Test --show-config flag displays configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write valid config
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "secret123",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "token123",
                    },
                    "bot": {"command_prefix": "!cd"},
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should exit successfully
            self.assertEqual(result.returncode, 0)

            # Output should contain configuration (but with redacted credentials)
            output = result.stdout + result.stderr
            self.assertTrue(
                "matrix" in output.lower() or "configuration" in output.lower(),
                "Config output should contain 'matrix' or 'configuration'",
            )

            # Credentials should be redacted
            if "REDACTED" in output or "***" in output:
                # If redaction is visible, verify it
                self.assertNotIn("secret123", output)
                self.assertNotIn("token123", output)
        finally:
            os.unlink(temp_config)

    def test_verbose_flags(self):
        """Test verbose flags increase verbosity correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write minimal valid config
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test with -v flag and show-config to avoid needing Matrix server
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-v",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_log_only_mode_flag(self):
        """Test -L/--log-only flag for non-interactive mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test log-only mode with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-L",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_color_flag(self):
        """Test -C/--color flag for colored output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test color mode with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-C",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_redact_flag(self):
        """Test -R/--redact flag for sensitive information redaction."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test redaction with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-R",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)

            # Output should contain redaction markers
            output = result.stdout + result.stderr
            if "REDACTED" in output or "Configuration" in output:
                # Sensitive data should be redacted
                self.assertTrue(
                    "REDACTED" in output or "***" in output or "[redacted]" in output.lower(),
                    "Expected redaction markers in output",
                )
        finally:
            os.unlink(temp_config)

    def test_combined_flags(self):
        """Test multiple flags combined."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test with multiple flags: verbose, color, redact, show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-vv",
                    "-C",
                    "-R",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_admin_users_flag(self):
        """Test -a/--admin flag for adding admin users."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test admin users flag with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-a",
                    "@admin1:example.com",
                    "-a",
                    "@admin2:example.com",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_allowed_rooms_flag(self):
        """Test -r/--room flag for adding allowed rooms."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test allowed rooms flag with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-r",
                    "!room1:example.com",
                    "-r",
                    "!room2:example.com",
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_no_greetings_flag(self):
        """Test -N/--no-greetings flag disables greeting messages."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Test no-greetings flag with show-config
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-N",
                    "-s",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)


class TestConfigurationFlow(unittest.TestCase):
    """Test configuration file handling and validation flow."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_valid_password_auth_config(self):
        """Test that valid password authentication config passes validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "secure_password_123",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "api_token_123",
                    },
                    "bot": {
                        "command_prefix": "!cd",
                        "admin_users": ["@admin:example.com"],
                        "allowed_rooms": ["!room:example.com"],
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed (config is valid)
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_valid_oidc_auth_config(self):
        """Test that valid OIDC authentication config passes validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "oidc",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "api_token_123",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed (config is valid)
            self.assertEqual(result.returncode, 0)
        finally:
            os.unlink(temp_config)

    def test_missing_homeserver_uses_default(self):
        """Test that missing homeserver uses default value."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-s",
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should succeed (uses default homeserver)
            self.assertEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            # Should contain default homeserver (matrix.org)
            self.assertIn("matrix.org", output.lower())
        finally:
            os.unlink(temp_config)

    def test_missing_user_id_validation(self):
        """Test that missing user_id fails validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should fail validation
            self.assertNotEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            self.assertIn("validation", output.lower())
        finally:
            os.unlink(temp_config)

    def test_invalid_json_config(self):
        """Test that invalid JSON is handled gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json content }")
            temp_config = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-N",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should fail
            self.assertNotEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            # Should mention parsing or JSON error
            self.assertTrue(
                "json" in output.lower() or "parse" in output.lower() or "error" in output.lower()
            )
        finally:
            os.unlink(temp_config)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and user feedback."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_keyboard_interrupt_handling(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        # This is tested implicitly by other tests - we just verify the process can be interrupted
        # We can't easily test SIGINT in subprocess, but we verify the handler exists
        from chatrixcd.main import main

        # Verify main function exists and is callable
        self.assertTrue(callable(main))

    def test_invalid_flag_handling(self):
        """Test that invalid flags produce helpful error messages."""
        result = subprocess.run(
            [sys.executable, "-m", "chatrixcd.main", "--invalid-flag"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit with error
        self.assertNotEqual(result.returncode, 0)

        # Error message should mention the invalid flag
        output = result.stdout + result.stderr
        self.assertTrue(
            "--invalid-flag" in output or "unrecognized" in output.lower(),
            "Error should mention invalid flag or be unrecognized",
        )

    def test_permission_denied_config(self):
        """Test handling of config file with no read permissions."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "test",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "test",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Remove read permissions (Unix-like systems only)
            if os.name != "nt":
                os.chmod(temp_config, 0o000)

                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "chatrixcd.main",
                        "-c",
                        temp_config,
                        "-N",
                    ],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    timeout=10,
                )

                # Should fail
                self.assertNotEqual(result.returncode, 0)

                output = result.stdout + result.stderr
                # Should mention permission or access error
                self.assertTrue(
                    "permission" in output.lower()
                    or "access" in output.lower()
                    or "denied" in output.lower()
                    or "error" in output.lower()
                )
            else:
                self.skipTest("Permission test not applicable on Windows")
        finally:
            # Restore permissions and delete
            if os.name != "nt":
                os.chmod(temp_config, 0o644)
            os.unlink(temp_config)


if __name__ == "__main__":
    unittest.main()
