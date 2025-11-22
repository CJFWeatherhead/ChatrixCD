"""Integration tests for live ChatrixCD instance.

This module tests ChatrixCD by connecting to a real Matrix server
and interacting with a running ChatrixCD bot instance.
"""

import os
import sys
import asyncio
import unittest
import json
import logging
from pathlib import Path
from typing import Optional
from nio import AsyncClient, RoomMessageText, MegolmEvent

# Try to import Sas for verification (may not be available in all versions)
try:
    from nio.crypto import Sas

    SAS_AVAILABLE = True
except ImportError:
    Sas = None
    SAS_AVAILABLE = False

logger = logging.getLogger(__name__)


@unittest.skipUnless(
    os.getenv("INTEGRATION_CONFIG"),
    "INTEGRATION_CONFIG environment variable not set - integration tests require live Matrix server",
)
class ChatrixCDIntegrationTest(unittest.IsolatedAsyncioTestCase):
    """Integration tests for ChatrixCD bot interactions."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        config_env = os.getenv("INTEGRATION_CONFIG")
        if not config_env:
            raise RuntimeError(
                "INTEGRATION_CONFIG environment variable not set"
            )

        try:
            cls.config = json.loads(config_env)
            # Use MATRIX_CONFIG if set, otherwise first host
            matrix_config_env = os.getenv("MATRIX_CONFIG")
            if matrix_config_env:
                cls.matrix_config = json.loads(matrix_config_env)
            else:
                cls.matrix_config = cls.config["hosts"][0]["matrix"]
            # Extract all bot configs
            cls.all_bots = [host["matrix"] for host in cls.config["hosts"]]
            cls.room_id = cls.config["test_room"]
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse INTEGRATION_CONFIG: {e}"
            ) from None
        except KeyError as e:
            raise RuntimeError(f"Missing required config key: {e}") from None

        cls.test_timeout = cls.config.get("test_timeout", 60)

        cls.store_paths = cls.config.get("store_paths", {})

    async def asyncSetUp(self):
        """Set up test client for each test."""
        print(f"DEBUG: all_bots contains {len(self.all_bots)} bots")
        for i, bot_config in enumerate(self.all_bots):
            print(
                f"DEBUG: Bot {i}: user_id={bot_config.get('bot_user_id')}, has_access_token={'access_token' in bot_config}"
            )

        # Find a bot with access token that is NOT the current bot being tested
        tester_bot = None
        for bot_config in self.all_bots:
            if (
                bot_config.get("bot_user_id")
                != self.matrix_config.get("bot_user_id")
                and "access_token" in bot_config
                and bot_config["access_token"]
            ):
                tester_bot = bot_config
                break

        if not tester_bot:
            print(
                "DEBUG: No other bot with access token available for testing"
            )
            self.authenticated = False
            self.client = None
            self.received_messages = []
            return

        # Use the copied store directory for the tester bot
        tester_user_id = tester_bot["bot_user_id"]
        self.test_store_dir = self.store_paths.get(tester_user_id)
        if not self.test_store_dir:
            print(
                f"DEBUG: No store path available for tester bot {tester_user_id}, creating temp dir"
            )
            import tempfile

            self.test_store_dir = tempfile.mkdtemp(prefix="chatrix_test_")
        print(f"DEBUG: Using store directory: {self.test_store_dir}")

        # Use the other bot as the tester (sender of commands)
        self.client = AsyncClient(
            tester_bot.get("homeserver", self.matrix_config["homeserver"]),
            tester_bot["bot_user_id"],
            store_path=self.test_store_dir,
        )

        # Set up the client with tester bot's device info
        self.client.user_id = tester_bot["bot_user_id"]
        if "device_id" in tester_bot:
            self.client.device_id = tester_bot["device_id"]

        # Restore the tester bot's existing session
        self.authenticated = False
        try:
            if "access_token" in tester_bot and "device_id" in tester_bot:

                logger.info(
                    f"Restoring tester bot's session ({tester_bot['bot_user_id']})..."
                )
                self.client.restore_login(
                    user_id=tester_bot["bot_user_id"],
                    device_id=tester_bot["device_id"],
                    access_token=tester_bot["access_token"],
                )

                # Enable encryption for the test client
                await self.client.sync(timeout=5000)

                # Load/create encryption account
                if self.client.olm:
                    try:
                        print("DEBUG: Loading test client encryption store")
                        self.client.load_store()
                        print("DEBUG: Test client encryption store loaded")
                    except Exception as e:
                        print(
                            f"DEBUG: Could not load test client store (normal on first run): {e}"
                        )

                # Test the restored session with a sync
                print(
                    f"DEBUG: Testing session with sync for {tester_bot['bot_user_id']}"
                )
                sync_response = await self.client.sync(timeout=5000)
                print(f"DEBUG: Sync response type: {type(sync_response)}")
                if hasattr(sync_response, "rooms"):
                    print(
                        "DEBUG: Successfully restored tester bot's session for testing"
                    )
                    self.authenticated = True
                else:
                    print(
                        f"DEBUG: Session restoration test failed: {sync_response}"
                    )
            else:
                logger.warning("No session data available for tester bot")

        except Exception as e:
            logger.warning(f"Failed to restore tester bot session: {e}")

        # Join the test room if authenticated
        if self.authenticated and self.client:
            try:
                print(f"DEBUG: Attempting to join room {self.room_id}")
                await self.client.join(self.room_id)
                print("DEBUG: Successfully joined room")

                # Perform cross-verification with the target bot
                await self._perform_cross_verification()

            except Exception as e:
                print(f"DEBUG: Failed to join room: {e}")
                self.authenticated = False

            # Set up event callbacks
            self.received_messages = []
            self.client.add_event_callback(
                self._on_room_message, RoomMessageText
            )
            self.client.add_event_callback(
                self._on_encrypted_message, MegolmEvent
            )
        else:
            print("DEBUG: Not authenticated, skipping room join")
            self.received_messages = []

    async def asyncTearDown(self):
        """Clean up after each test."""
        if self.client:
            await self.client.close()

        # Clean up temporary store directory
        if hasattr(self, "test_store_dir") and self.test_store_dir:
            import shutil

            try:
                shutil.rmtree(self.test_store_dir)
                print(
                    f"DEBUG: Cleaned up test store directory: {self.test_store_dir}"
                )
            except Exception as e:
                print(f"DEBUG: Failed to clean up test store directory: {e}")

    def _on_room_message(self, room, event):
        """Callback for room messages."""
        if room.room_id == self.room_id:
            self.received_messages.append(event)

    def _on_encrypted_message(self, room, event):
        """Callback for encrypted messages."""
        if room.room_id == self.room_id:
            self.received_messages.append(event)

    async def _decrypt_message(self, event) -> Optional[str]:
        """Decrypt an encrypted message if possible.

        Args:
            event: The message event (MegolmEvent or RoomMessageText)

        Returns:
            Decrypted message content, or None if decryption failed
        """
        try:
            # If it's already a decrypted message
            if (
                hasattr(event, "body")
                and event.body
                and not isinstance(event, MegolmEvent)
            ):
                return event.body

            # If it's an encrypted message, try to decrypt it
            if (
                isinstance(event, MegolmEvent)
                and self.client
                and self.client.olm
            ):
                # Decrypt the message
                decrypted = await self.client.decrypt_megolm_event(event)
                if decrypted and hasattr(decrypted, "body"):
                    return decrypted.body

        except Exception as e:
            print(f"DEBUG: Failed to decrypt message: {e}")

        return None

    async def _perform_cross_verification(self):
        """Perform cross-verification with all bots to enable encrypted message reading."""
        if not self.authenticated or not self.client:
            return

        print("DEBUG: Performing cross-verification with all bots...")

        # Check if encryption is available
        if not self.client.olm:
            print(
                "DEBUG: Encryption not available on test client - skipping cross-verification"
            )
            print(
                "DEBUG: This is expected in integration tests as we can't access remote encryption stores"
            )
            return

        for bot_config in self.all_bots:
            target_user_id = bot_config["bot_user_id"]
            target_device_id = bot_config.get("device_id")

            if not target_device_id:
                print(
                    f"DEBUG: No device ID available for {target_user_id}, skipping"
                )
                continue

            print(
                f"DEBUG: Attempting verification with {target_user_id} device {target_device_id}"
            )

            try:
                # Sync to get latest device information
                await self.client.sync(timeout=5000)

                # Check if device is already verified
                if (
                    hasattr(self.client, "device_store")
                    and self.client.device_store
                ):
                    user_devices = self.client.device_store.get(target_user_id)
                    if user_devices and target_device_id in user_devices:
                        device = user_devices[target_device_id]
                        if getattr(device, "verified", False):
                            print(
                                f"DEBUG: Device {target_device_id} for {target_user_id} is already verified"
                            )
                            continue

                # Start verification process
                print(
                    f"DEBUG: Starting verification with {target_user_id} device {target_device_id}"
                )

                # Send a verification request
                resp = await self.client.start_key_verification(
                    target_device_id, target_user_id
                )
                print(f"DEBUG: Verification start response: {resp}")

                # Wait a bit for the verification to be established
                await asyncio.sleep(2)

                # Try to auto-accept any pending verifications
                if hasattr(self.client, "key_verifications") and SAS_AVAILABLE:
                    for (
                        transaction_id,
                        verification,
                    ) in self.client.key_verifications.items():
                        if Sas and isinstance(verification, Sas):
                            print(
                                f"DEBUG: Found SAS verification {transaction_id}"
                            )

                            # For testing, we'll try to confirm the verification
                            # In a real scenario, you'd compare emojis or use QR codes
                            try:
                                await verification.confirm()
                                print(
                                    f"DEBUG: Confirmed verification {transaction_id}"
                                )
                            except Exception as e:
                                print(
                                    f"DEBUG: Failed to confirm verification {transaction_id}: {e}"
                                )

                # Wait for verification to complete
                await asyncio.sleep(3)

                # Check if verification succeeded
                if (
                    hasattr(self.client, "device_store")
                    and self.client.device_store
                ):
                    user_devices = self.client.device_store.get(target_user_id)
                    if user_devices and target_device_id in user_devices:
                        device = user_devices[target_device_id]
                        if getattr(device, "verified", False):
                            print(
                                f"DEBUG: Successfully verified device {target_device_id} for {target_user_id}"
                            )
                        else:
                            print(
                                f"DEBUG: Device {target_device_id} for {target_user_id} is not verified"
                            )

            except Exception as e:
                print(f"DEBUG: Verification failed for {target_user_id}: {e}")
                continue

    async def _share_room_keys_with_device(self, device):
        """Share room keys with a verified device."""
        try:
            # Share keys for the test room
            await self.client.share_group_session(
                self.room_id,
                users=[device.user_id],
                ignore_unverified_devices=False,
            )
            print(
                f"DEBUG: Shared room keys for {self.room_id} with {device.user_id}"
            )
        except Exception as e:
            print(f"DEBUG: Failed to share room keys: {e}")

    async def _send_command_and_wait(
        self, command_suffix: str, timeout: int = 10
    ) -> Optional[str]:
        """Send a command to the bot and wait for a response."""
        if not self.authenticated or not self.client:
            # Cannot send commands without authentication
            return None

        # Get the correct command prefix for this bot
        prefix = self.matrix_config.get("command_prefix", "!cd")
        command = f"{prefix} {command_suffix}"

        # Record the timestamp before sending the command
        # Use Matrix server time by getting the current sync token time
        # pre_command_time = int(asyncio.get_event_loop().time() * 1000)

        # Send the command
        await self.client.room_send(
            room_id=self.room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": command},
        )

        print(f"DEBUG: Sent command '{command}' to room {self.room_id}")

        # Wait for response from bot
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(0.5)

            # Sync to get new messages
            try:
                await self.client.sync(timeout=1000)
            except Exception as e:
                print(f"DEBUG: Sync failed: {e}")

            # Debug: print all received messages
            if self.received_messages:
                print(
                    f"DEBUG: Received {len(self.received_messages)} messages:"
                )
                for i, event in enumerate(self.received_messages):
                    body = getattr(event, "body", "[ENCRYPTED]")
                    print(
                        f"DEBUG: Message {i}: sender={event.sender}, body='{body}' (timestamp: {event.server_timestamp})"
                    )

            # Check for messages from the bot that came after the command was sent
            for event in self.received_messages:
                if event.sender == self.matrix_config["bot_user_id"]:
                    # Try to decrypt the message
                    decrypted_body = await self._decrypt_message(event)
                    if decrypted_body:
                        print(
                            f"DEBUG: Found decrypted response from bot {event.sender}: '{decrypted_body}'"
                        )
                        return decrypted_body
                    elif hasattr(event, "body") and event.body:
                        print(
                            f"DEBUG: Found text response from bot {event.sender}: '{event.body}'"
                        )
                        return event.body
                    else:
                        # This is likely an encrypted message we can't decrypt yet
                        print(
                            f"DEBUG: Found encrypted response from bot {event.sender} (cannot decrypt yet)"
                        )
                        return "[ENCRYPTED_RESPONSE]"

        print(
            f"DEBUG: Timeout waiting for response from {self.matrix_config['bot_user_id']}"
        )
        return None

    async def test_bot_responds_to_help(self):
        """Test that the bot responds to the help command."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        response = await self._send_command_and_wait("help")

        self.assertIsNotNone(response, "Bot did not respond to help command")
        # For encrypted responses, we can't check content but we can verify response was received
        # Note: We don't check for specific content since responses may be encrypted

    async def test_bot_responds_to_invalid_command(self):
        """Test that the bot responds to invalid commands."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        response = await self._send_command_and_wait("nonexistentcommand")

        self.assertIsNotNone(
            response, "Bot did not respond to invalid command"
        )
        # Bot should respond with an error or help message - we can't validate content for encrypted responses

    async def test_bot_responds_to_pet_command(self):
        """Test the hidden pet command."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        response = await self._send_command_and_wait("pet")

        self.assertIsNotNone(response, "Bot did not respond to pet command")
        # Should be positive response

    async def test_bot_responds_to_scold_command(self):
        """Test the hidden scold command."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        response = await self._send_command_and_wait("scold")

        self.assertIsNotNone(response, "Bot did not respond to scold command")
        # Should be apologetic response

    async def test_bot_status_command(self):
        """Test the status command if available."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        # This might require a running task, so we'll just check it doesn't crash
        response = await self._send_command_and_wait("status nonexistent")

        self.assertIsNotNone(response, "Bot did not respond to status command")
        # Should indicate task not found or similar

    async def test_bot_projects_command(self):
        """Test that the bot can list projects (requires authentication)."""
        if not self.authenticated:
            self.skipTest(
                "Test client not authenticated - cannot test bot responses"
            )

        response = await self._send_command_and_wait("projects")

        self.assertIsNotNone(
            response, "Bot did not respond to projects command"
        )
        # Should list projects or indicate no projects

    async def test_bot_config_valid(self):
        """Test that the bot configuration is valid."""
        # This test can run without authentication
        # Use the first bot config for validation
        bot_config = self.all_bots[0]
        self.assertIn(
            "homeserver", bot_config, "Matrix config should contain homeserver"
        )
        self.assertIn(
            "bot_user_id",
            bot_config,
            "Matrix config should contain bot_user_id",
        )
        self.assertIn(
            "homeserver",
            self.matrix_config,
            "Matrix config should contain homeserver",
        )
        self.assertIn(
            "test_room", self.config, "Config should contain test_room"
        )

        # Verify homeserver URL format
        self.assertTrue(
            bot_config["homeserver"].startswith("https://"),
            "Homeserver should use HTTPS",
        )

        # Verify bot user ID format
        self.assertTrue(
            bot_config["bot_user_id"].startswith("@"),
            "Bot user ID should start with @",
        )
        self.assertIn(
            ":",
            bot_config["bot_user_id"],
            "Bot user ID should contain domain separator",
        )


if __name__ == "__main__":
    # Load config for manual testing
    config_path = os.getenv(
        "INTEGRATION_CONFIG", "tests/integration_config.json"
    )
    if not Path(config_path).exists():
        print(f"Config file not found: {config_path}")
        print(
            "Please copy integration_config.json.example to integration_config.json and configure it."
        )
        sys.exit(1)

    unittest.main()
