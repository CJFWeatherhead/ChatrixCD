"""Tests for verification cancellation handling.

This module tests that verification cancellations are properly tracked
and handled in daemon/log modes.
"""

import asyncio
import unittest
from unittest.mock import MagicMock

from chatrixcd.verification import DeviceVerificationManager


class TestVerificationCancellation(unittest.TestCase):
    """Test verification cancellation tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.client.olm = MagicMock()
        self.client.device_store = MagicMock()
        self.client.key_verifications = {}
        self.manager = DeviceVerificationManager(self.client)

    def test_handle_verification_cancellation(self):
        """Test that cancellation tracking works."""
        # Track a cancellation
        asyncio.run(
            self.manager.handle_verification_cancellation(
                "test_tx_id", "@user:example.com", "User cancelled", "m.user"
            )
        )

        # Verify it's tracked
        self.assertTrue(self.manager.should_show_manual_verification_message("test_tx_id"))

        # Verify we can get the info
        info = self.manager.get_cancellation_info("test_tx_id")
        self.assertIsNotNone(info)
        self.assertEqual(info["user_id"], "@user:example.com")
        self.assertEqual(info["reason"], "User cancelled")
        self.assertEqual(info["code"], "m.user")
        self.assertIn("timestamp", info)

    def test_clear_cancelled_verification(self):
        """Test that cancelled verifications can be cleared."""
        # Track a cancellation
        asyncio.run(
            self.manager.handle_verification_cancellation("test_tx_id", "@user:example.com")
        )

        # Clear it
        self.manager.clear_cancelled_verification("test_tx_id")

        # Verify it's cleared
        self.assertFalse(self.manager.should_show_manual_verification_message("test_tx_id"))

    def test_cancelled_verification_not_found(self):
        """Test checking for non-existent cancelled verification."""
        # Should return False for unknown transaction
        self.assertFalse(self.manager.should_show_manual_verification_message("unknown_tx"))

        # Should return None for unknown transaction info
        self.assertIsNone(self.manager.get_cancellation_info("unknown_tx"))

    def test_multiple_cancellations(self):
        """Test tracking multiple cancellations."""
        # Track multiple cancellations
        asyncio.run(
            self.manager.handle_verification_cancellation(
                "tx1", "@user1:example.com", "User cancelled", "m.user"
            )
        )
        asyncio.run(
            self.manager.handle_verification_cancellation(
                "tx2", "@user2:example.com", "Timeout", "m.timeout"
            )
        )

        # Both should be tracked
        self.assertTrue(self.manager.should_show_manual_verification_message("tx1"))
        self.assertTrue(self.manager.should_show_manual_verification_message("tx2"))

        # Clear one
        self.manager.clear_cancelled_verification("tx1")

        # Only tx2 should remain
        self.assertFalse(self.manager.should_show_manual_verification_message("tx1"))
        self.assertTrue(self.manager.should_show_manual_verification_message("tx2"))


if __name__ == "__main__":
    unittest.main()
