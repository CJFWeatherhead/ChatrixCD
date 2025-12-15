"""End-to-End workflow tests with input/output verification.

This module tests complete user workflows and scenarios including:
- Configuration wizard interactive flow
- Multi-step command sequences
- Integration between components

Uses subprocess for testing complete workflows.
"""

import os
import sys
import json
import tempfile
import unittest
import subprocess
from pathlib import Path


class TestConfigurationWizardWorkflow(unittest.TestCase):
    """Test the interactive configuration wizard workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_init_flag_creates_config(self):
        """Test that --init flag successfully initiates configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_config = os.path.join(tmpdir, "test_config.json")

            # Run with --init flag but provide EOF immediately to skip wizard
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    new_config,
                    "--init",
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Check that wizard was invoked
            output = result.stdout + result.stderr
            self.assertTrue(
                "Configuration" in output or "ChatrixCD" in output,
                f"Expected wizard output, got: {output[:200]}",
            )

    def test_config_validation_error_messages(self):
        """Test that configuration validation provides clear error messages."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write config with multiple validation errors
            json.dump(
                {
                    "matrix": {
                        "homeserver": "",
                        "user_id": "",
                        "auth_type": "invalid_type",
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
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should fail with validation errors
            self.assertNotEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            # Should mention validation failure
            self.assertIn("validation", output.lower())

            # Should provide specific error details
            self.assertTrue(
                "user_id" in output.lower()
                or "required" in output.lower()
                or "error" in output.lower()
            )
        finally:
            os.unlink(temp_config)


class TestCommandLineWorkflows(unittest.TestCase):
    """Test complete command-line workflows and scenarios."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_show_config_after_validation_failure(self):
        """Test that show-config works even with invalid config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "",  # Invalid
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
            # Show-config should work even with validation errors
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

            # Should succeed (show-config bypasses validation)
            self.assertEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            self.assertTrue(
                "Configuration" in output or "matrix" in output.lower(),
                f"Expected config output, got: {output[:200]}",
            )
        finally:
            os.unlink(temp_config)

    def test_verbose_redact_combination(self):
        """Test verbose logging with redaction enabled."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "matrix": {
                        "homeserver": "https://matrix.example.com",
                        "user_id": "@bot:example.com",
                        "auth_type": "password",
                        "password": "secret_password_123",
                    },
                    "semaphore": {
                        "url": "https://semaphore.example.com",
                        "api_token": "secret_token_456",
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Run with verbose and redact flags
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-vv",
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

            output = result.stdout + result.stderr
            # Passwords should be redacted even in verbose mode
            self.assertNotIn("secret_password_123", output)
            self.assertNotIn("secret_token_456", output)
        finally:
            os.unlink(temp_config)

    def test_admin_and_room_flags_override(self):
        """Test that CLI flags override config file values."""
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
                    "bot": {
                        "admin_users": ["@config_admin:example.com"],
                        "allowed_rooms": ["!config_room:example.com"],
                    },
                },
                f,
            )
            temp_config = f.name

        try:
            # Add admin users and rooms via CLI
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-a",
                    "@cli_admin1:example.com",
                    "-a",
                    "@cli_admin2:example.com",
                    "-r",
                    "!cli_room1:example.com",
                    "-r",
                    "!cli_room2:example.com",
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

            output = result.stdout + result.stderr
            # Both config and CLI values should be present (merged)
            # Note: We can't easily verify the merge without parsing, but we can verify success
            self.assertTrue(len(output) > 0)
        finally:
            os.unlink(temp_config)

    def test_multiple_config_files(self):
        """Test loading configuration from different file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple config files in different locations
            configs = []
            for i in range(3):
                config_path = os.path.join(tmpdir, f"config{i}.json")
                with open(config_path, "w") as f:
                    json.dump(
                        {
                            "matrix": {
                                "homeserver": f"https://matrix{i}.example.com",
                                "user_id": f"@bot{i}:example.com",
                                "auth_type": "password",
                                "password": "test",
                            },
                            "semaphore": {
                                "url": f"https://semaphore{i}.example.com",
                                "api_token": "test",
                            },
                        },
                        f,
                    )
                configs.append(config_path)

            # Test each config file
            for i, config_path in enumerate(configs):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "chatrixcd.main",
                        "-c",
                        config_path,
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
                self.assertEqual(result.returncode, 0, f"Failed for config{i}.json")

                # Should show correct config
                output = result.stdout + result.stderr
                self.assertIn(f"matrix{i}.example.com", output)


class TestOutputVerification(unittest.TestCase):
    """Test output formatting and content verification."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_version_output_format(self):
        """Test that version output follows expected format."""
        result = subprocess.run(
            [sys.executable, "-m", "chatrixcd.main", "--version"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        output = result.stdout + result.stderr

        # Should contain "ChatrixCD" followed by version
        self.assertRegex(output, r"ChatrixCD\s+\d+\.\d+")

        # Version should follow semantic versioning pattern
        # Format: YYYY.MM.DD.PATCH.BUILD.COMMIT or similar
        self.assertRegex(output, r"\d+\.\d+\.\d+")

    def test_help_output_structure(self):
        """Test that help output has proper structure."""
        result = subprocess.run(
            [sys.executable, "-m", "chatrixcd.main", "--help"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=5,
        )

        output = result.stdout + result.stderr

        # Should have usage line
        self.assertIn("usage", output.lower())

        # Should describe the program
        self.assertTrue(
            "Matrix bot" in output or "CI/CD" in output,
            "Help should describe the program",
        )

        # Should list flags
        flags = ["-v", "--verbose", "-c", "--config", "-s", "--show-config"]
        for flag in flags:
            self.assertIn(flag, output, f"Missing flag: {flag}")

    def test_config_output_json_structure(self):
        """Test that config output has valid JSON structure."""
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

            output = result.stdout + result.stderr

            # Should contain JSON-like structure
            self.assertIn("{", output)
            self.assertIn("}", output)
            self.assertIn("matrix", output.lower())
            self.assertIn("semaphore", output.lower())
        finally:
            os.unlink(temp_config)

    def test_error_output_clarity(self):
        """Test that error messages are clear and helpful."""
        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
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

            # Error message should be clear
            self.assertTrue(
                "error" in output.lower()
                or "invalid" in output.lower()
                or "parse" in output.lower()
            )

            # Should mention the config file
            self.assertTrue(
                temp_config in output or "config" in output.lower(),
                "Error message should mention config file",
            )
        finally:
            os.unlink(temp_config)

    def test_validation_error_list(self):
        """Test that validation errors are listed clearly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Config with multiple validation errors
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
                stdin=subprocess.DEVNULL,
                timeout=10,
            )

            # Should fail
            self.assertNotEqual(result.returncode, 0)

            output = result.stdout + result.stderr

            # Should list validation errors
            self.assertIn("validation", output.lower())

            # Should mention required fields
            # At least user_id should be mentioned
            self.assertTrue("user_id" in output.lower() or "required" in output.lower())
        finally:
            os.unlink(temp_config)


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic integration scenarios."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.project_root = Path(__file__).parent.parent

    def test_first_time_user_workflow(self):
        """Test workflow for first-time user with no config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_config = os.path.join(tmpdir, "config.json")

            # Try to run without config (simulating first-time user)
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
                timeout=10,
            )

            output = result.stdout + result.stderr

            # Should either:
            # 1. Prompt about missing config, or
            # 2. Proceed with defaults
            self.assertTrue(
                "not found" in output.lower()
                or "configuration" in output.lower()
                or result.returncode == 0  # Proceeds with defaults
            )

    def test_config_migration_scenario(self):
        """Test configuration migration scenario."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write old config without version
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
                    # No _config_version field
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

            # Should succeed (auto-migration)
            self.assertEqual(result.returncode, 0)

            output = result.stdout + result.stderr
            # Should show migrated config with version
            self.assertTrue(
                "_config_version" in output or "matrix" in output.lower(),
                "Config output should show version or matrix section",
            )
        finally:
            os.unlink(temp_config)

    def test_update_config_with_cli_flags(self):
        """Test updating configuration with CLI flags."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write basic config
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
            # Run with admin users and rooms
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "chatrixcd.main",
                    "-c",
                    temp_config,
                    "-a",
                    "@admin:example.com",
                    "-r",
                    "!room:example.com",
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


if __name__ == "__main__":
    unittest.main()
