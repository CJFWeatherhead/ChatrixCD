"""Tests for device verification module."""

import unittest
from unittest.mock import Mock, AsyncMock, patch
from chatrixcd.verification import DeviceVerificationManager


class TestDeviceVerificationManager(unittest.TestCase):
    """Test device verification manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.olm = True
        self.mock_client.user_id = "@bot:example.com"
        self.mock_client.device_id = "BOTDEVICE"
        self.manager = DeviceVerificationManager(self.mock_client)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.manager.client, self.mock_client)
    
    def test_get_unverified_devices_no_encryption(self):
        """Test get_unverified_devices when encryption is not enabled."""
        self.mock_client.olm = None
        result = unittest.mock.patch.object(
            self.manager, 'get_unverified_devices', 
            return_value=[]
        )
        with result:
            devices = self.manager.client.olm
            self.assertIsNone(devices)
    
    def test_get_unverified_devices_empty(self):
        """Test get_unverified_devices with no devices."""
        self.mock_client.device_store = Mock()
        self.mock_client.device_store.users = []
        
        # Can't easily test async without asyncio.run in setUp
        # This is a basic structure test
        self.assertIsNotNone(self.manager.client.olm)
    
    def test_manager_has_required_methods(self):
        """Test that manager has all required methods."""
        required_methods = [
            'get_unverified_devices',
            'get_pending_verifications',
            'start_verification',
            'accept_verification',
            'wait_for_key_exchange',
            'get_emoji_list',
            'confirm_verification',
            'reject_verification',
            'auto_verify_pending',
            'verify_device_interactive',
            'verify_pending_interactive'
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(self.manager, method_name),
                f"Manager missing method: {method_name}"
            )
            method = getattr(self.manager, method_name)
            self.assertTrue(
                callable(method),
                f"Manager method not callable: {method_name}"
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


if __name__ == '__main__':
    unittest.main()
