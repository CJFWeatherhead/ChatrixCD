"""End-to-End tests for device verification.

This module tests the full verification flow between two clients,
including SAS emoji verification and encrypted message exchange.
"""

import unittest
from unittest.mock import Mock, AsyncMock
from typing import Any
from nio import AsyncClient

# Conditional import for Sas - not available in all nio versions
try:
    from nio.crypto import Sas, OlmDevice, SasState

    SAS_AVAILABLE = True
except ImportError:
    SAS_AVAILABLE = False
    Sas = Any  # type: ignore
    OlmDevice = Any  # type: ignore
    SasState = Any  # type: ignore
from nio.crypto.device import TrustState
from nio.responses import ToDeviceResponse, ToDeviceMessage
from chatrixcd.verification import DeviceVerificationManager


def create_mock_to_device_response():
    """Create a mock ToDeviceResponse for testing."""
    mock_message = Mock(spec=ToDeviceMessage)
    return ToDeviceResponse(mock_message)


@unittest.skipIf(not SAS_AVAILABLE, "Sas not available in this nio version")
class TestDeviceVerificationE2E(unittest.IsolatedAsyncioTestCase):
    """End-to-end tests for device verification workflow."""

    async def asyncSetUp(self):
        """Set up test fixtures for each test."""
        # Create mock clients for two devices
        self.client_alice = Mock(spec=AsyncClient)
        self.client_alice.user_id = "@alice:example.com"
        self.client_alice.device_id = "ALICE_DEVICE"
        self.client_alice.olm = True
        self.client_alice.key_verifications = {}

        self.client_bob = Mock(spec=AsyncClient)
        self.client_bob.user_id = "@bob:example.com"
        self.client_bob.device_id = "BOB_DEVICE"
        self.client_bob.olm = True
        self.client_bob.key_verifications = {}

        # Create verification managers for both clients
        self.manager_alice = DeviceVerificationManager(self.client_alice)
        self.manager_bob = DeviceVerificationManager(self.client_bob)

    async def test_get_pending_verifications_with_sas(self):
        """Test getting pending verifications with proper user_id and device_id."""
        # Create a mock OlmDevice for Bob
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"
        bob_device.display_name = "Bob's Device"

        # Create a mock SAS verification object
        sas = Mock(spec=Sas)
        sas.other_olm_device = bob_device
        sas.transaction_id = "test_transaction_123"
        sas.state = SasState.created
        sas.we_started_it = False

        # Add to Alice's key_verifications
        self.client_alice.key_verifications = {"test_transaction_123": sas}

        # Get pending verifications
        pending = await self.manager_alice.get_pending_verifications()

        # Verify the results
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["transaction_id"], "test_transaction_123")
        self.assertEqual(pending[0]["user_id"], "@bob:example.com")
        self.assertEqual(pending[0]["device_id"], "BOB_DEVICE")
        self.assertEqual(pending[0]["type"], "Mock")
        self.assertIsNotNone(pending[0]["verification"])

    async def test_accept_verification_sends_to_device_messages(self):
        """Test that accepting verification sends to-device messages."""
        # Create a mock SAS verification
        sas = Mock(spec=Sas)
        sas.transaction_id = "test_transaction_456"
        sas.state = SasState.created
        sas.we_started_it = False

        # Mock the client methods
        self.client_alice.accept_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client_alice.send_to_device_messages = AsyncMock()

        # Accept the verification
        result = await self.manager_alice.accept_verification(sas)

        # Verify the result
        self.assertTrue(result)
        self.client_alice.accept_key_verification.assert_called_once_with("test_transaction_456")
        self.client_alice.send_to_device_messages.assert_called_once()

    async def test_start_verification_sends_to_device_messages(self):
        """Test that starting verification sends to-device messages."""
        # Create a mock device
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"

        # Create a mock SAS that will be returned
        sas = Mock(spec=Sas)
        sas.transaction_id = "test_transaction_789"
        sas.other_olm_device = bob_device

        # Mock the client methods
        self.client_alice.start_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client_alice.send_to_device_messages = AsyncMock()
        self.client_alice.key_verifications = {"test_transaction_789": sas}

        # Start verification
        result = await self.manager_alice.start_verification(bob_device)

        # Verify the result
        self.assertIsNotNone(result)
        self.client_alice.start_key_verification.assert_called_once_with(bob_device)
        self.client_alice.send_to_device_messages.assert_called_once()

    async def test_full_verification_flow_mock(self):
        """Test the full verification flow from start to finish (mocked)."""
        # Create mock devices
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"
        bob_device.display_name = "Bob's Device"

        alice_device = Mock(spec=OlmDevice)
        alice_device.user_id = "@alice:example.com"
        alice_device.id = "ALICE_DEVICE"
        alice_device.display_name = "Alice's Device"

        # Create mock SAS objects for both sides
        sas_alice = Mock(spec=Sas)
        sas_alice.transaction_id = "shared_transaction"
        sas_alice.other_olm_device = bob_device
        sas_alice.state = SasState.created
        sas_alice.we_started_it = True
        sas_alice.other_key_set = True
        sas_alice.get_emoji = Mock(return_value=[("🐶", "Dog"), ("🎉", "Party"), ("🌟", "Star")])
        sas_alice.accept_sas = Mock()

        sas_bob = Mock(spec=Sas)
        sas_bob.transaction_id = "shared_transaction"
        sas_bob.other_olm_device = alice_device
        sas_bob.state = SasState.created
        sas_bob.we_started_it = False
        sas_bob.other_key_set = True
        sas_bob.get_emoji = Mock(return_value=[("🐶", "Dog"), ("🎉", "Party"), ("🌟", "Star")])
        sas_bob.accept_sas = Mock()

        # Setup mock client methods
        self.client_alice.start_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client_alice.send_to_device_messages = AsyncMock()
        self.client_alice.key_verifications = {"shared_transaction": sas_alice}

        self.client_bob.accept_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client_bob.send_to_device_messages = AsyncMock()
        self.client_bob.key_verifications = {"shared_transaction": sas_bob}

        # Step 1: Alice starts verification with Bob
        sas_result_alice = await self.manager_alice.start_verification(bob_device)
        self.assertIsNotNone(sas_result_alice)
        self.client_alice.start_key_verification.assert_called_once()
        self.client_alice.send_to_device_messages.assert_called()

        # Step 2: Bob accepts the verification request
        accept_result = await self.manager_bob.accept_verification(sas_bob)
        self.assertTrue(accept_result)
        self.client_bob.accept_key_verification.assert_called_once()
        self.client_bob.send_to_device_messages.assert_called()

        # Step 3: Both wait for key exchange (simulated by setting other_key_set=True above)
        alice_key_ready = await self.manager_alice.wait_for_key_exchange(sas_alice, max_wait=1)
        bob_key_ready = await self.manager_bob.wait_for_key_exchange(sas_bob, max_wait=1)
        self.assertTrue(alice_key_ready)
        self.assertTrue(bob_key_ready)

        # Step 4: Both get emoji lists
        alice_emojis = await self.manager_alice.get_emoji_list(sas_alice)
        bob_emojis = await self.manager_bob.get_emoji_list(sas_bob)
        self.assertEqual(alice_emojis, bob_emojis)
        self.assertEqual(len(alice_emojis), 3)

        # Step 5: Both confirm the verification
        alice_confirm = await self.manager_alice.confirm_verification(sas_alice)
        bob_confirm = await self.manager_bob.confirm_verification(sas_bob)
        self.assertTrue(alice_confirm)
        self.assertTrue(bob_confirm)

        # Verify that accept_sas was called on both SAS objects
        sas_alice.accept_sas.assert_called_once()
        sas_bob.accept_sas.assert_called_once()

        # Verify that send_to_device_messages was called multiple times
        # (start, accept, confirm)
        self.assertGreaterEqual(self.client_alice.send_to_device_messages.call_count, 2)
        self.assertGreaterEqual(self.client_bob.send_to_device_messages.call_count, 2)

    async def test_auto_verify_pending_sends_messages(self):
        """Test that auto-verification sends to-device messages."""
        # Create a mock SAS verification
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"

        sas = Mock(spec=Sas)
        sas.transaction_id = "auto_verify_transaction"
        sas.other_olm_device = bob_device
        sas.state = SasState.created
        sas.we_started_it = False
        sas.other_key_set = True
        sas.accept_sas = Mock()

        # Setup mock client
        self.client_alice.key_verifications = {"auto_verify_transaction": sas}
        self.client_alice.accept_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client_alice.send_to_device_messages = AsyncMock()

        # Auto-verify
        result = await self.manager_alice.auto_verify_pending("auto_verify_transaction")

        # Verify the result
        self.assertTrue(result)
        self.client_alice.accept_key_verification.assert_called_once_with("auto_verify_transaction")
        # Should be called twice: once for accept, once for confirm
        self.assertEqual(self.client_alice.send_to_device_messages.call_count, 2)
        sas.accept_sas.assert_called_once()

    async def test_verification_with_wrong_emojis_rejection(self):
        """Test that verification can be rejected when emojis don't match."""
        # Create a mock SAS with key exchange complete
        sas = Mock(spec=Sas)
        sas.transaction_id = "reject_transaction"
        sas.other_key_set = True
        sas.reject_sas = Mock()

        # Setup mock client
        self.client_alice.send_to_device_messages = AsyncMock()

        # Reject the verification
        result = await self.manager_alice.reject_verification(sas)

        # Verify the result
        self.assertTrue(result)
        sas.reject_sas.assert_called_once()
        self.client_alice.send_to_device_messages.assert_called_once()

    async def test_verification_timeout_when_key_not_received(self):
        """Test that verification times out when other device's key is not received."""
        # Create a mock SAS without key exchange
        sas = Mock(spec=Sas)
        sas.transaction_id = "timeout_transaction"
        sas.other_key_set = False  # Key never set

        # Wait for key exchange with short timeout
        result = await self.manager_alice.wait_for_key_exchange(sas, max_wait=1)

        # Verify it timed out
        self.assertFalse(result)

    async def test_get_pending_verifications_with_unknown_fallback(self):
        """Test that Unknown is used as fallback when device info is not available."""
        # Create a mock verification without proper device info
        # This simulates a non-Sas verification type or corrupt data
        mock_verification = Mock()
        # Remove the default Mock behavior for user_id and device_id
        # by using a spec that doesn't have these attributes
        del mock_verification.user_id
        del mock_verification.device_id

        self.client_alice.key_verifications = {"unknown_transaction": mock_verification}

        # Get pending verifications
        pending = await self.manager_alice.get_pending_verifications()

        # Verify fallback to 'Unknown'
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["user_id"], "Unknown")
        self.assertEqual(pending[0]["device_id"], "Unknown")


@unittest.skipIf(not SAS_AVAILABLE, "Sas not available in this nio version")
class TestVerificationInteractiveFlow(unittest.IsolatedAsyncioTestCase):
    """Test interactive verification flows."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.client = Mock(spec=AsyncClient)
        self.client.user_id = "@alice:example.com"
        self.client.device_id = "ALICE_DEVICE"
        self.client.olm = True
        self.client.key_verifications = {}
        self.manager = DeviceVerificationManager(self.client)

    async def test_verify_device_interactive_success(self):
        """Test successful interactive device verification."""
        # Create mock device and SAS
        device = Mock(spec=OlmDevice)
        device.user_id = "@bob:example.com"
        device.id = "BOB_DEVICE"

        sas = Mock(spec=Sas)
        sas.transaction_id = "interactive_transaction"
        sas.other_olm_device = device
        sas.state = SasState.created
        sas.we_started_it = True
        sas.other_key_set = True
        sas.get_emoji = Mock(return_value=[("🎉", "Party")])
        sas.accept_sas = Mock()

        # Mock client methods
        self.client.start_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client.send_to_device_messages = AsyncMock()
        self.client.key_verifications = {"interactive_transaction": sas}

        # Create a callback that confirms emojis match
        async def emoji_callback(emoji_list):
            self.assertEqual(emoji_list, [("🎉", "Party")])
            return True  # User confirms emojis match

        # Verify device interactively
        device_info = {"device": device}
        result = await self.manager.verify_device_interactive(device_info, emoji_callback)

        # Verify success
        self.assertTrue(result)
        sas.accept_sas.assert_called_once()
        self.assertGreaterEqual(self.client.send_to_device_messages.call_count, 2)

    async def test_verify_device_interactive_rejection(self):
        """Test interactive device verification with user rejection."""
        # Create mock device and SAS
        device = Mock(spec=OlmDevice)
        device.user_id = "@bob:example.com"
        device.id = "BOB_DEVICE"

        sas = Mock(spec=Sas)
        sas.transaction_id = "reject_interactive_transaction"
        sas.other_olm_device = device
        sas.state = SasState.created
        sas.we_started_it = True
        sas.other_key_set = True
        sas.get_emoji = Mock(return_value=[("🎉", "Party")])
        sas.reject_sas = Mock()

        # Mock client methods
        self.client.start_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client.send_to_device_messages = AsyncMock()
        self.client.key_verifications = {"reject_interactive_transaction": sas}

        # Create a callback that rejects emojis
        async def emoji_callback(emoji_list):
            return False  # User says emojis don't match

        # Verify device interactively
        device_info = {"device": device}
        result = await self.manager.verify_device_interactive(device_info, emoji_callback)

        # Verify rejection
        self.assertTrue(result)
        sas.reject_sas.assert_called_once()
        self.client.send_to_device_messages.assert_called()


@unittest.skipIf(not SAS_AVAILABLE, "Sas not available in this nio version")
class TestVerificationPersistence(unittest.IsolatedAsyncioTestCase):
    """Test verification status persistence features."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.client = Mock(spec=AsyncClient)
        self.client.user_id = "@alice:example.com"
        self.client.device_id = "ALICE_DEVICE"
        self.client.olm = True
        self.client.device_store = Mock()
        self.client.verify_device = Mock()
        self.manager = DeviceVerificationManager(self.client)

    async def test_get_verified_devices(self):
        """Test getting list of verified devices."""
        # Create mock verified device
        verified_device = Mock(spec=OlmDevice)
        verified_device.user_id = "@bob:example.com"
        verified_device.id = "BOB_DEVICE"
        verified_device.display_name = "Bob's Phone"
        verified_device.verified = True
        verified_device.trust_state = TrustState.verified

        # Create mock unverified device
        unverified_device = Mock(spec=OlmDevice)
        unverified_device.user_id = "@charlie:example.com"
        unverified_device.id = "CHARLIE_DEVICE"
        unverified_device.display_name = "Charlie's Laptop"
        unverified_device.verified = False
        unverified_device.trust_state = TrustState.unset

        # Setup device store
        self.client.device_store.users = [
            "@bob:example.com",
            "@charlie:example.com",
        ]
        self.client.device_store.__getitem__ = Mock(
            side_effect=lambda user_id: {
                "@bob:example.com": {"BOB_DEVICE": verified_device},
                "@charlie:example.com": {"CHARLIE_DEVICE": unverified_device},
            }[user_id]
        )

        # Get verified devices
        verified = await self.manager.get_verified_devices()

        # Should only return Bob's verified device
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["user_id"], "@bob:example.com")
        self.assertEqual(verified[0]["device_id"], "BOB_DEVICE")
        self.assertEqual(verified[0]["device_name"], "Bob's Phone")
        self.assertEqual(verified[0]["trust_state"], TrustState.verified)

    async def test_is_device_verified_true(self):
        """Test checking if a specific device is verified (verified case)."""
        # Create mock verified device
        verified_device = Mock(spec=OlmDevice)
        verified_device.verified = True

        # Setup device store
        self.client.device_store.users = ["@bob:example.com"]
        self.client.device_store.__getitem__ = Mock(return_value={"BOB_DEVICE": verified_device})

        # Check if device is verified
        result = await self.manager.is_device_verified("@bob:example.com", "BOB_DEVICE")

        self.assertTrue(result)

    async def test_is_device_verified_false(self):
        """Test checking if a specific device is verified (unverified case)."""
        # Create mock unverified device
        unverified_device = Mock(spec=OlmDevice)
        unverified_device.verified = False

        # Setup device store
        self.client.device_store.users = ["@bob:example.com"]
        self.client.device_store.__getitem__ = Mock(return_value={"BOB_DEVICE": unverified_device})

        # Check if device is verified
        result = await self.manager.is_device_verified("@bob:example.com", "BOB_DEVICE")

        self.assertFalse(result)

    async def test_is_device_verified_device_not_found(self):
        """Test checking verification for non-existent device."""
        # Setup empty device store
        self.client.device_store.users = []

        # Check if device is verified
        result = await self.manager.is_device_verified("@bob:example.com", "BOB_DEVICE")

        self.assertFalse(result)

    async def test_confirm_verification_persists_device(self):
        """Test that confirming verification persists device trust."""
        # Create mock device and SAS
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"

        sas = Mock(spec=Sas)
        sas.other_key_set = True
        sas.other_olm_device = bob_device
        sas.accept_sas = Mock()

        # Mock client methods
        self.client.send_to_device_messages = AsyncMock()

        # Confirm verification
        result = await self.manager.confirm_verification(sas)

        # Verify success
        self.assertTrue(result)
        sas.accept_sas.assert_called_once()
        self.client.send_to_device_messages.assert_called_once()

        # Verify that verify_device was called to persist the trust
        self.client.verify_device.assert_called_once_with(bob_device)

    async def test_auto_verify_pending_persists_device(self):
        """Test that auto-verification persists device trust."""
        # Create mock device and SAS
        bob_device = Mock(spec=OlmDevice)
        bob_device.user_id = "@bob:example.com"
        bob_device.id = "BOB_DEVICE"

        sas = Mock(spec=Sas)
        sas.transaction_id = "auto_persist_transaction"
        sas.other_olm_device = bob_device
        sas.state = SasState.created
        sas.we_started_it = False
        sas.other_key_set = True
        sas.accept_sas = Mock()

        # Setup mock client
        self.client.key_verifications = {"auto_persist_transaction": sas}
        self.client.accept_key_verification = AsyncMock(
            return_value=create_mock_to_device_response()
        )
        self.client.send_to_device_messages = AsyncMock()

        # Auto-verify
        result = await self.manager.auto_verify_pending("auto_persist_transaction")

        # Verify success
        self.assertTrue(result)

        # Verify that verify_device was called to persist the trust
        self.client.verify_device.assert_called_once_with(bob_device)

    async def test_get_verified_devices_no_encryption(self):
        """Test getting verified devices when encryption is disabled."""
        self.client.olm = None

        verified = await self.manager.get_verified_devices()

        self.assertEqual(len(verified), 0)

    async def test_is_device_verified_no_encryption(self):
        """Test checking device verification when encryption is disabled."""
        self.client.olm = None

        result = await self.manager.is_device_verified("@bob:example.com", "BOB_DEVICE")

        self.assertFalse(result)

    async def test_get_verified_devices_filters_own_device(self):
        """Test that get_verified_devices filters out the bot's own device."""
        # Create mock verified device (the bot's own device)
        own_device = Mock(spec=OlmDevice)
        own_device.user_id = "@alice:example.com"
        own_device.id = "ALICE_DEVICE"
        own_device.verified = True
        own_device.trust_state = TrustState.verified

        # Setup device store with only own device
        self.client.device_store.users = ["@alice:example.com"]
        self.client.device_store.__getitem__ = Mock(return_value={"ALICE_DEVICE": own_device})

        # Get verified devices
        verified = await self.manager.get_verified_devices()

        # Should not include own device
        self.assertEqual(len(verified), 0)


if __name__ == "__main__":
    unittest.main()
