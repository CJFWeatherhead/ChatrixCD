"""Tests for device info logging in daemon/log modes."""

import asyncio
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from chatrixcd.bot import ChatrixBot
from chatrixcd.config import Config


class TestDeviceInfoLogging(unittest.TestCase):
    """Test device information logging."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock config
        self.config = MagicMock(spec=Config)
        self.config.config = {}  # Add config attribute for plugin manager
        self.config.get_matrix_config.return_value = {
            "homeserver": "https://matrix.example.com",
            "user_id": "@testbot:example.com",
            "device_id": "TESTDEVICE",
            "device_name": "Test Bot",
            "store_path": "/tmp/test_store",
        }
        self.config.get_semaphore_config.return_value = {
            "url": "https://semaphore.example.com",
            "api_token": "test_token",
        }
        self.config.get_bot_config.return_value = {
            "command_prefix": "!cd",
        }
        self.config.get.return_value = True

    def test_log_device_info_daemon_mode(self):
        """Test device info logging in daemon mode."""
        # Create bot in daemon mode
        bot = ChatrixBot(self.config, mode="daemon")

        # Mock encryption being enabled
        mock_olm = MagicMock()
        mock_device_store = MagicMock()
        
        # Create mock device
        mock_device = MagicMock()
        mock_device.ed25519 = "ABCD1234EFGH5678IJKL9012MNOP3456"
        mock_device.display_name = "Test Bot"

        # Mock device_store structure
        mock_device_store.users = ["@testbot:example.com"]
        mock_device_store.__getitem__.return_value = {
            "TESTDEVICE": mock_device
        }

        # Patch bot.client.olm and device_store access
        with patch.object(bot.client, "olm", mock_olm), \
             patch("chatrixcd.bot.logger") as mock_logger:
            
            # Mock device_store as a property that returns our mock
            type(bot.client).device_store = PropertyMock(return_value=mock_device_store)
            
            asyncio.run(bot._log_device_info())

            # Verify logger.info was called with device information
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]

            # Check that the output contains expected information
            self.assertIn("Bot Device Information", call_args)
            self.assertIn("@testbot:example.com", call_args)
            self.assertIn("TESTDEVICE", call_args)
            self.assertIn("ABCD1234EFGH5678IJKL9012MNOP3456", call_args)
            self.assertIn("/verify", call_args)

    def test_log_device_info_log_mode(self):
        """Test device info logging in log mode."""
        # Create bot in log mode
        bot = ChatrixBot(self.config, mode="log")

        # Mock encryption being enabled
        mock_olm = MagicMock()
        mock_device_store = MagicMock()
        
        # Create mock device
        mock_device = MagicMock()
        mock_device.ed25519 = "TEST_FINGERPRINT_12345"
        mock_device.display_name = "Test Bot Log Mode"

        # Mock device_store structure
        mock_device_store.users = ["@testbot:example.com"]
        mock_device_store.__getitem__.return_value = {
            "TESTDEVICE": mock_device
        }

        # Patch bot.client.olm and device_store access
        with patch.object(bot.client, "olm", mock_olm), \
             patch("chatrixcd.bot.logger") as mock_logger:
            
            # Mock device_store as a property that returns our mock
            type(bot.client).device_store = PropertyMock(return_value=mock_device_store)
            
            asyncio.run(bot._log_device_info())

            # Verify logger.info was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]

            # Check that the output contains expected information
            self.assertIn("Bot Device Information", call_args)
            self.assertIn("TEST_FINGERPRINT_12345", call_args)

    def test_log_device_info_no_encryption(self):
        """Test device info logging with encryption disabled."""
        # Create bot in daemon mode
        bot = ChatrixBot(self.config, mode="daemon")

        # Mock encryption being disabled
        bot.client.olm = None

        # Call the method - should return early without error
        with patch("chatrixcd.bot.logger") as mock_logger:
            asyncio.run(bot._log_device_info())

            # Verify logger.info was NOT called (no encryption)
            mock_logger.info.assert_not_called()

    def test_log_device_info_tui_mode_not_called(self):
        """Test that device info is not logged in TUI mode."""
        # Create bot in TUI mode
        bot = ChatrixBot(self.config, mode="tui")

        # Mock encryption being enabled
        bot.client.olm = MagicMock()

        # Mock setup_encryption to verify _log_device_info is not called in TUI mode
        with patch.object(bot, "_log_device_info") as mock_log_device:
            # Call setup_encryption
            asyncio.run(bot.setup_encryption())

            # Verify _log_device_info was NOT called in TUI mode
            mock_log_device.assert_not_called()


if __name__ == "__main__":
    unittest.main()
