"""Tests for device verification module."""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from chatrixcd.verification import DeviceVerificationManager, SAS_AVAILABLE


class TestDeviceVerificationManager(unittest.IsolatedAsyncioTestCase):
    """Test device verification manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.olm = Mock()
        self.mock_client.user_id = "@bot:example.com"
        self.mock_client.device_id = "BOTDEVICE"
        self.manager = DeviceVerificationManager(self.mock_client)

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.manager.client, self.mock_client)

    async def test_get_unverified_devices_no_encryption(self):
        """Test get_unverified_devices when encryption is not enabled."""
        self.mock_client.olm = None
        devices = await self.manager.get_unverified_devices()
        self.assertEqual(devices, [])

    async def test_get_unverified_devices_empty(self):
        """Test get_unverified_devices with no device store."""
        self.mock_client.device_store = None
        devices = await self.manager.get_unverified_devices()
        self.assertEqual(devices, [])

    async def test_get_unverified_devices_with_devices(self):
        """Test get_unverified_devices with actual devices."""
        # Mock device store
        mock_device_store = Mock()
        user_devices = {
            "DEVICE1": Mock(verified=False, display_name="Device 1"),
            "DEVICE2": Mock(verified=True, display_name="Device 2"),
        }
        mock_device_store.users = {"@user1:example.com": user_devices}
        # Configure __getitem__ to return user devices
        mock_device_store.__getitem__ = Mock(return_value=user_devices)

        self.mock_client.device_store = mock_device_store

        devices = await self.manager.get_unverified_devices()

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["user_id"], "@user1:example.com")
        self.assertEqual(devices[0]["device_id"], "DEVICE1")
        self.assertEqual(devices[0]["device_name"], "Device 1")

    async def test_get_pending_verifications(self):
        """Test get_pending_verifications."""
        # Mock key verifications
        mock_sas = Mock()
        mock_sas.other_olm_device = Mock(
            user_id="@user:example.com", id="DEVICE1"
        )
        # Also set on the verification object for non-SAS case
        mock_sas.user_id = "@user:example.com"
        mock_sas.device_id = "DEVICE1"

        self.mock_client.key_verifications = {"txn1": mock_sas}

        pending = await self.manager.get_pending_verifications()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["transaction_id"], "txn1")
        self.assertEqual(pending[0]["user_id"], "@user:example.com")
        self.assertEqual(pending[0]["device_id"], "DEVICE1")

    async def test_start_verification_no_sas(self):
        """Test start_verification when SAS is not available."""
        with patch("chatrixcd.verification.SAS_AVAILABLE", False):
            device = Mock()
            result = await self.manager.start_verification(device)
            self.assertIsNone(result)

    async def test_auto_verify_pending_no_sas(self):
        """Test auto_verify_pending when SAS is not available."""
        with patch("chatrixcd.verification.SAS_AVAILABLE", False):
            result = await self.manager.auto_verify_pending("txn1")
            self.assertFalse(result)

    @unittest.skipIf(
        not SAS_AVAILABLE, "Sas not available in this nio version"
    )
    async def test_cross_verify_with_bots(self):
        """Test cross_verify_with_bots."""
        room_members = [
            "@user1:example.com",
            "@chatrixbot:example.com",
            "@otherbot:example.com",
        ]

        # Mock get_unverified_devices to return bot devices
        mock_devices = [
            {
                "user_id": "@chatrixbot:example.com",
                "device_id": "BOTDEVICE1",
                "device": Mock(),
            },
            {
                "user_id": "@otherbot:example.com",
                "device_id": "BOTDEVICE2",
                "device": Mock(),
            },
        ]

        # Mock start_verification to return a mock SAS
        mock_sas = Mock()
        with (
            patch.object(
                self.manager,
                "get_unverified_devices",
                return_value=mock_devices,
            ),
            patch.object(
                self.manager, "start_verification", return_value=mock_sas
            ) as mock_start,
        ):
            count = await self.manager.cross_verify_with_bots(room_members)

            # Should have called start_verification for the bot users
            self.assertEqual(
                mock_start.call_count, 2
            )  # chatrixbot and otherbot
            self.assertEqual(count, 2)

    async def test_save_session_state(self):
        """Test save_session_state."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            filepath = f.name

        try:
            # Mock device store
            mock_device_store = Mock()
            user_devices = {
                "DEVICE1": Mock(
                    ed25519="ed25519_key",  # Use string instead of bytes
                    curve25519="curve25519_key",  # Use string instead of bytes
                    verified=True,
                    display_name="Device 1",
                )
            }
            mock_device_store.users = {"@user1:example.com": user_devices}
            # Configure __getitem__ to return the user devices
            mock_device_store.__getitem__ = Mock(return_value=user_devices)

            self.mock_client.device_store = mock_device_store
            success = await self.manager.save_session_state(filepath)
            self.assertTrue(success)

            # Check file was created and has expected content
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, "r") as f:
                data = f.read()
                self.assertIn("@user1:example.com", data)
                self.assertIn("DEVICE1", data)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    async def test_load_session_state(self):
        """Test load_session_state."""
        session_data = {
            "verified_devices": [
                {"user_id": "@user1:example.com", "device_id": "DEVICE1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            import json

            json.dump(session_data, f)
            filepath = f.name

        try:
            # Mock device store
            mock_device_store = Mock()
            mock_device = Mock()
            user_devices = {"DEVICE1": mock_device}
            mock_device_store.users = {"@user1:example.com": user_devices}
            # Configure __getitem__ to return the user devices
            mock_device_store.__getitem__ = Mock(return_value=user_devices)

            self.mock_client.device_store = mock_device_store
            success = await self.manager.load_session_state(filepath)
            self.assertTrue(success)

            # Check that verify_device was called
            self.mock_client.verify_device.assert_called_once_with(mock_device)

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_manager_has_required_methods(self):
        """Test that manager has all required methods."""
        required_methods = [
            "get_unverified_devices",
            "get_pending_verifications",
            "start_verification",
            "accept_verification",
            "wait_for_key_exchange",
            "get_emoji_list",
            "confirm_verification",
            "reject_verification",
            "auto_verify_pending",
            "verify_device_interactive",
            "verify_pending_interactive",
            "cross_verify_with_bots",
            "save_session_state",
            "load_session_state",
        ]

        for method_name in required_methods:
            self.assertTrue(
                hasattr(self.manager, method_name),
                f"Manager missing method: {method_name}",
            )
            method = getattr(self.manager, method_name)
            self.assertTrue(
                callable(method), f"Manager method not callable: {method_name}"
            )


class TestVerificationModuleImport(unittest.TestCase):
    """Test that verification module can be imported."""

    def test_import_verification_module(self):
        """Test importing verification module."""
        from chatrixcd import verification

        self.assertIsNotNone(verification)

    def test_import_device_verification_manager(self):
        """Test importing DeviceVerificationManager class."""
        from chatrixcd.verification import DeviceVerificationManager

        self.assertIsNotNone(DeviceVerificationManager)


if __name__ == "__main__":
    unittest.main()
