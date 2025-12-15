"""Device verification module for ChatrixCD.

This module provides reusable verification functionality across TUI, CLI, and daemon modes.
It handles SAS (emoji) verification following the Matrix specification for device trust.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Tuple
from nio import AsyncClient, ToDeviceError

# Try to import Sas for device verification
# These may not be available in all versions of matrix-nio
try:
    from nio.crypto import Sas, SasState

    SAS_AVAILABLE = True
except ImportError:
    # Fallback for older versions or when crypto is not available
    Sas = None  # type: ignore
    SasState = None  # type: ignore
    SAS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeviceVerificationManager:
    """Manager for device verification workflows.

    This class provides reusable device verification logic that can be used in:
    - TUI mode: Interactive verification with UI callbacks
    - CLI mode: Command-line verification with text prompts
    - Daemon mode: Automatic verification without user interaction
    """

    def __init__(self, client: AsyncClient):
        """Initialize the verification manager.

        Args:
            client: Matrix client instance with encryption enabled
        """
        self.client = client
        # Track cancelled/failed verifications to show manual verification message
        self.cancelled_verifications: Dict[str, Dict[str, str]] = {}

    async def get_verified_devices(self) -> List[Dict[str, Any]]:
        """Get list of verified devices.

        Returns:
            List of verified device dictionaries with user_id, device_id,
            device_name, trust_state, and device object
        """
        if not self.client.olm:
            logger.warning(
                "Encryption not enabled, cannot get verified devices"
            )
            return []

        verified_devices = []

        try:
            if (
                hasattr(self.client, "device_store")
                and self.client.device_store
            ):
                for user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    for device_id, device in user_devices.items():
                        # Skip our own device
                        if (
                            user_id == self.client.user_id
                            and device_id == self.client.device_id
                        ):
                            continue
                        # Only include verified devices
                        if getattr(device, "verified", False):
                            verified_devices.append(
                                {
                                    "user_id": user_id,
                                    "device_id": device_id,
                                    "device_name": getattr(
                                        device, "display_name", "Unknown"
                                    ),
                                    "trust_state": getattr(
                                        device, "trust_state", None
                                    ),
                                    "device": device,
                                }
                            )
        except Exception as e:
            logger.error(f"Error getting verified devices: {e}")

        return verified_devices

    async def handle_verification_cancellation(
        self,
        transaction_id: str,
        user_id: str,
        reason: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """Handle verification cancellation events.

        This method is called when a verification request is cancelled by either party.
        It tracks the cancellation and can be used to display manual verification messages.

        Args:
            transaction_id: Transaction ID of the cancelled verification
            user_id: User ID who cancelled or whose verification was cancelled
            reason: Optional reason for cancellation
            code: Optional cancellation code (e.g., 'm.user', 'm.timeout')
        """
        self.cancelled_verifications[transaction_id] = {
            "user_id": user_id,
            "reason": reason or "Unknown",
            "code": code or "Unknown",
            "timestamp": time.time(),
        }
        logger.info(
            f"Verification {transaction_id} cancelled by {user_id} "
            f"(code: {code}, reason: {reason})"
        )

    def should_show_manual_verification_message(
        self, transaction_id: str
    ) -> bool:
        """Check if manual verification message should be shown.

        Args:
            transaction_id: Transaction ID to check

        Returns:
            True if manual verification message should be shown
        """
        return transaction_id in self.cancelled_verifications

    def get_cancellation_info(self, transaction_id: str) -> Optional[Dict[str, str]]:
        """Get cancellation information for a transaction.

        Args:
            transaction_id: Transaction ID to check

        Returns:
            Dict with user_id, reason, code, timestamp if cancelled, None otherwise
        """
        return self.cancelled_verifications.get(transaction_id)

    def clear_cancelled_verification(self, transaction_id: str) -> None:
        """Clear a cancelled verification from tracking.

        Args:
            transaction_id: Transaction ID to clear
        """
        self.cancelled_verifications.pop(transaction_id, None)

    async def is_device_verified(self, user_id: str, device_id: str) -> bool:
        """Check if a specific device is verified.

        Args:
            user_id: User ID of the device owner
            device_id: Device ID to check

        Returns:
            True if device is verified, False otherwise
        """
        if not self.client.olm:
            return False

        try:
            if (
                hasattr(self.client, "device_store")
                and self.client.device_store
            ):
                if user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    if device_id in user_devices:
                        device = user_devices[device_id]
                        return getattr(device, "verified", False)
        except Exception as e:
            logger.error(f"Error checking device verification: {e}")

        return False

    async def get_unverified_devices(self) -> List[Dict[str, Any]]:
        """Get list of unverified devices.

        Returns:
            List of unverified device dictionaries with user_id, device_id,
            device_name, and device object
        """
        if not self.client.olm:
            logger.warning(
                "Encryption not enabled, cannot get unverified devices"
            )
            return []

        unverified_devices = []

        try:
            if (
                hasattr(self.client, "device_store")
                and self.client.device_store
            ):
                for user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    for device_id, device in user_devices.items():
                        # Skip our own device
                        if (
                            user_id == self.client.user_id
                            and device_id == self.client.device_id
                        ):
                            continue
                        # Only include unverified devices
                        if not getattr(device, "verified", False):
                            unverified_devices.append(
                                {
                                    "user_id": user_id,
                                    "device_id": device_id,
                                    "device_name": getattr(
                                        device, "display_name", "Unknown"
                                    ),
                                    "device": device,
                                }
                            )
        except Exception as e:
            logger.error(f"Error getting unverified devices: {e}")

        return unverified_devices

    async def get_pending_verifications(self) -> List[Dict[str, Any]]:
        """Get list of pending verification requests.

        Returns:
            List of pending verification dictionaries with transaction_id,
            user_id, device_id, type, and verification object
        """
        pending = []

        if (
            hasattr(self.client, "key_verifications")
            and self.client.key_verifications
        ):
            for (
                transaction_id,
                verification,
            ) in self.client.key_verifications.items():
                # For Sas verifications, user_id and device_id are in other_olm_device
                if Sas and isinstance(verification, Sas):
                    other_device = getattr(
                        verification, "other_olm_device", None
                    )
                    if other_device:
                        user_id = getattr(other_device, "user_id", "Unknown")
                        device_id = getattr(other_device, "id", "Unknown")
                    else:
                        user_id = "Unknown"
                        device_id = "Unknown"
                else:
                    user_id = getattr(verification, "user_id", "Unknown")
                    device_id = getattr(verification, "device_id", "Unknown")

                pending.append(
                    {
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "device_id": device_id,
                        "type": type(verification).__name__,
                        "verification": verification,
                    }
                )

        return pending

    async def start_verification(self, device: Any) -> Optional[Any]:
        """Start SAS verification with a device.

        Args:
            device: Device object from device_store

        Returns:
            SAS verification object if successful, None otherwise
        """
        if not SAS_AVAILABLE:
            logger.warning(
                "SAS verification not available in this version of matrix-nio"
            )
            return None

        try:
            # Start key verification
            resp = await self.client.start_key_verification(device)

            if isinstance(resp, ToDeviceError):
                logger.error(f"Failed to start verification: {resp.message}")
                return None

            # Send the start message to the other device
            await self.client.send_to_device_messages()

            # Wait for the verification to be set up
            await asyncio.sleep(1)

            # Get the SAS object from the client
            if hasattr(self.client, "key_verifications"):
                for (
                    transaction_id,
                    verification,
                ) in self.client.key_verifications.items():
                    if Sas and isinstance(verification, Sas):
                        if verification.other_olm_device == device:
                            return verification

            logger.warning(
                "Verification started, but could not retrieve SAS object"
            )
            return None

        except Exception as e:
            logger.error(f"Error starting verification: {e}")
            return None

    async def accept_verification(self, sas: Any) -> bool:
        """Accept a verification request.

        Args:
            sas: SAS verification object

        Returns:
            True if accepted successfully, False otherwise
        """
        if not SAS_AVAILABLE:
            logger.warning(
                "SAS verification not available in this version of matrix-nio"
            )
            return False

        try:
            if (
                not sas.we_started_it
                and SasState
                and sas.state == SasState.created
            ):
                await self.client.accept_key_verification(sas.transaction_id)
                # Send the accept message to the other device
                await self.client.send_to_device_messages()
                await asyncio.sleep(0.5)
                return True
            return True
        except Exception as e:
            logger.error(f"Error accepting verification: {e}")
            return False

    async def wait_for_key_exchange(
        self, sas: Any, max_wait: int = 10
    ) -> bool:
        """Wait for key exchange to complete.

        Args:
            sas: SAS verification object
            max_wait: Maximum seconds to wait

        Returns:
            True if key exchange completed, False if timeout
        """
        wait_time = 0
        while not sas.other_key_set and wait_time < max_wait:
            await asyncio.sleep(0.5)
            wait_time += 0.5

        return sas.other_key_set

    async def get_emoji_list(
        self, sas: Any
    ) -> Optional[List[Tuple[str, str]]]:
        """Get emoji list from SAS verification.

        Args:
            sas: SAS verification object

        Returns:
            List of (emoji, description) tuples, or None on error
        """
        try:
            return sas.get_emoji()
        except Exception as e:
            logger.error(f"Error getting emojis: {e}")
            return None

    async def confirm_verification(self, sas: Any) -> bool:
        """Confirm the SAS verification (emojis match).

        This method confirms the verification and persists the device's verified
        status to the store for future sessions. It also shares room keys with
        the newly verified device.

        Args:
            sas: SAS verification object

        Returns:
            True if confirmed successfully, False otherwise
        """
        try:
            if not sas.other_key_set:
                logger.error(
                    "Cannot confirm verification: Key exchange not complete"
                )
                return False

            sas.accept_sas()
            await self.client.send_to_device_messages()

            # Mark the device as verified in the store for persistence
            # This ensures the verified status is saved and remembered across restarts
            if sas.other_olm_device:
                self.client.verify_device(sas.other_olm_device)
                logger.info(
                    f"Verified and persisted trust for device {sas.other_olm_device.id} "
                    f"of user {sas.other_olm_device.user_id}"
                )

                # Share room keys with the newly verified device
                # This allows the device to decrypt messages in encrypted rooms
                await self._share_room_keys_with_device(sas.other_olm_device)

            logger.info("Verification confirmed successfully")
            return True

        except Exception as e:
            logger.error(f"Error confirming verification: {e}")
            return False

    async def _share_room_keys_with_device(self, device):
        """Share room keys with a device after verification.

        This method shares the Megolm session keys for all encrypted rooms
        with a newly verified device, allowing it to decrypt future messages.

        Args:
            device: The OlmDevice to share keys with
        """
        try:
            # Get all rooms the user is in
            shared_rooms = []
            for room_id, room in self.client.rooms.items():
                # Check if this is an encrypted room and the user is a member
                if room.encrypted and device.user_id in room.users:
                    shared_rooms.append(room_id)

            if not shared_rooms:
                logger.debug(
                    f"No encrypted rooms shared with {device.user_id}, "
                    "skipping room key sharing"
                )
                return

            logger.info(
                f"Sharing room keys for {len(shared_rooms)} encrypted room(s) "
                f"with verified device {device.id} of user {device.user_id}"
            )

            # Share keys for each room
            for room_id in shared_rooms:
                try:
                    # Share the group session for this room with the device
                    await self.client.share_group_session(
                        room_id,
                        users=[device.user_id],
                        ignore_unverified_devices=False,
                    )
                    logger.debug(
                        f"Shared room key for room {room_id} with {device.user_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to share room key for room {room_id}: {e}"
                    )

            # Send the to-device messages to actually deliver the keys
            await self.client.send_to_device_messages()

            logger.info(
                f"Successfully shared room keys with {device.user_id}'s device {device.id}"
            )

        except Exception as e:
            logger.error(f"Error sharing room keys with device: {e}")

    async def reject_verification(self, sas: Any) -> bool:
        """Reject the SAS verification (emojis don't match).

        Args:
            sas: SAS verification object

        Returns:
            True if rejected successfully, False otherwise
        """
        try:
            if not sas.other_key_set:
                logger.error(
                    "Cannot reject verification: Key exchange not complete"
                )
                return False

            sas.reject_sas()
            await self.client.send_to_device_messages()
            logger.info("Verification rejected")
            return True

        except Exception as e:
            logger.error(f"Error rejecting verification: {e}")
            return False

    async def auto_verify_pending(self, transaction_id: str, max_wait: int = 5) -> bool:
        """Automatically verify a pending verification request (daemon mode).

        This method auto-verifies devices and shares room keys with them.
        Includes retry logic to wait for matrix-nio to process the verification event.

        Args:
            transaction_id: Transaction ID of the verification request
            max_wait: Maximum seconds to wait for verification object (default: 5)

        Returns:
            True if auto-verified successfully, False otherwise
        """
        try:
            # Wait for the SAS verification object to be available
            # matrix-nio needs time to process the KeyVerificationStart event
            sas = None
            waited = 0.0
            retry_interval = 0.5
            
            while waited < max_wait:
                # Check if verification was cancelled while we were waiting
                if transaction_id in self.cancelled_verifications:
                    logger.info(
                        f"Verification {transaction_id} was cancelled before we could accept it"
                    )
                    return False
                
                if (
                    hasattr(self.client, "key_verifications")
                    and transaction_id in self.client.key_verifications
                ):
                    sas = self.client.key_verifications[transaction_id]
                    if Sas and isinstance(sas, Sas):
                        logger.debug(
                            f"Found SAS verification object for {transaction_id} "
                            f"after {waited:.1f}s"
                        )
                        break
                
                await asyncio.sleep(retry_interval)
                waited += retry_interval
            
            if not sas:
                # Check if it was cancelled during our wait
                if transaction_id in self.cancelled_verifications:
                    cancel_info = self.cancelled_verifications[transaction_id]
                    logger.info(
                        f"Verification {transaction_id} was cancelled "
                        f"(reason: {cancel_info['reason']})"
                    )
                else:
                    logger.warning(
                        f"Cannot auto-verify: verification {transaction_id} not found "
                        f"after waiting {max_wait}s (may have timed out)"
                    )
                return False

            if not (Sas and isinstance(sas, Sas)):
                logger.warning(
                    f"Cannot auto-verify: {transaction_id} is not a SAS verification "
                    f"or SAS not available"
                )
                return False

            # Accept the verification request
            await self.client.accept_key_verification(transaction_id)
            # Send the accept message to the other device
            await self.client.send_to_device_messages()
            logger.info(f"Auto-accepted verification request {transaction_id}")

            # Wait for key exchange
            await asyncio.sleep(1)

            # Check if verification was cancelled during key exchange
            if transaction_id in self.cancelled_verifications:
                cancel_info = self.cancelled_verifications[transaction_id]
                logger.warning(
                    f"Verification {transaction_id} was cancelled during key exchange "
                    f"(reason: {cancel_info['reason']})"
                )
                return False

            # Automatically accept the SAS (trust without emoji comparison)
            if sas.other_key_set:
                sas.accept_sas()
                await self.client.send_to_device_messages()

                # Mark the device as verified in the store for persistence
                if sas.other_olm_device:
                    self.client.verify_device(sas.other_olm_device)
                    logger.info(
                        f"Auto-verified and persisted trust for device {sas.other_olm_device.id} "
                        f"of user {sas.other_olm_device.user_id} in transaction {transaction_id}"
                    )

                    # Share room keys with the newly verified device
                    await self._share_room_keys_with_device(
                        sas.other_olm_device
                    )
                else:
                    logger.info(
                        f"Auto-verified device in transaction {transaction_id}"
                    )
                
                # Clear from cancelled tracking if it was there
                self.clear_cancelled_verification(transaction_id)
                return True
            else:
                logger.warning(
                    f"Cannot auto-verify {transaction_id}: other device key not received"
                )
                return False

        except Exception as e:
            logger.error(f"Error during auto-verification: {e}", exc_info=True)
            return False

    async def verify_device_interactive(
        self,
        device_info: Dict[str, Any],
        emoji_callback: Callable[[List[Tuple[str, str]]], bool],
    ) -> bool:
        """Verify a device interactively (CLI/TUI mode).

        This method coordinates the full verification flow:
        1. Start verification with device
        2. Wait for key exchange
        3. Get emoji list
        4. Call callback to display emojis and get user confirmation
        5. Confirm or reject based on callback result

        Args:
            device_info: Device information dictionary with 'device' key
            emoji_callback: Async callable that displays emojis and returns True if match

        Returns:
            True if device verified successfully, False otherwise
        """
        device = device_info["device"]

        # Start verification
        sas = await self.start_verification(device)
        if not sas:
            logger.error("Failed to start verification")
            return False

        # Accept if needed
        if not await self.accept_verification(sas):
            logger.error("Failed to accept verification")
            return False

        # Wait for key exchange
        if not await self.wait_for_key_exchange(sas):
            logger.error(
                "Verification timeout: Did not receive other device's key"
            )
            return False

        # Get emoji list
        emoji_list = await self.get_emoji_list(sas)
        if not emoji_list:
            logger.error("Failed to get emoji list")
            return False

        # Call callback to display and get user confirmation
        try:
            user_confirmed = await emoji_callback(emoji_list)
        except Exception as e:
            logger.error(f"Error in emoji callback: {e}")
            return False

        # Confirm or reject based on user response
        if user_confirmed:
            return await self.confirm_verification(sas)
        else:
            return await self.reject_verification(sas)

    async def verify_pending_interactive(
        self,
        verification_info: Dict[str, Any],
        emoji_callback: Callable[[List[Tuple[str, str]]], bool],
    ) -> bool:
        """Verify a pending verification request interactively.

        Args:
            verification_info: Verification info dictionary with 'verification' key
            emoji_callback: Async callable that displays emojis and returns True if match

        Returns:
            True if verified successfully, False otherwise
        """
        verification = verification_info["verification"]

        if not (Sas and isinstance(verification, Sas)):
            logger.error(
                f"Unsupported verification type or SAS not available: {verification_info['type']}"
            )
            return False

        sas = verification

        # Accept if needed
        if not await self.accept_verification(sas):
            logger.error("Failed to accept verification")
            return False

        # Wait for key exchange
        if not await self.wait_for_key_exchange(sas):
            logger.error(
                "Verification timeout: Did not receive other device's key"
            )
            return False

        # Get emoji list
        emoji_list = await self.get_emoji_list(sas)
        if not emoji_list:
            logger.error("Failed to get emoji list")
            return False

        # Call callback to display and get user confirmation
        try:
            user_confirmed = await emoji_callback(emoji_list)
        except Exception as e:
            logger.error(f"Error in emoji callback: {e}")
            return False

        # Confirm or reject based on user response
        if user_confirmed:
            return await self.confirm_verification(sas)
        else:
            return await self.reject_verification(sas)

    async def cross_verify_with_bots(self, room_members: List[str]) -> int:
        """Cross-verify with other ChatrixCD bots in a room.

        This method identifies other ChatrixCD bots and automatically starts
        verification with their devices.

        Args:
            room_members: List of user IDs in the room

        Returns:
            Number of verification requests started
        """
        if not SAS_AVAILABLE:
            logger.warning(
                "SAS verification not available, cannot cross-verify"
            )
            return 0

        # Find potential bot users
        potential_bots = []
        for user_id in room_members:
            if (
                "chatrix" in user_id.lower()
                or "sparkles" in user_id.lower()
                or "opsbot" in user_id.lower()
                or "bot" in user_id.lower()
            ):
                potential_bots.append(user_id)

        if len(potential_bots) <= 1:
            logger.debug(
                "No other potential bots found for cross-verification"
            )
            return 0

        logger.info(
            f"Found {len(potential_bots)} potential bots for cross-verification"
        )

        # Get unverified devices for these users
        unverified_devices = await self.get_unverified_devices()
        bot_devices = [
            d for d in unverified_devices if d["user_id"] in potential_bots
        ]

        if not bot_devices:
            logger.debug("All potential bot devices are already verified")
            return 0

        # Start verification with each unverified bot device
        started_count = 0
        for device_info in bot_devices:
            try:
                sas = await self.start_verification(device_info["device"])
                if sas:
                    started_count += 1
                    logger.info(
                        f"Started cross-verification with {device_info['user_id']}'s "
                        f"device {device_info['device_id']}"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to start cross-verification with {device_info['user_id']}: {e}"
                )

        return started_count

    async def save_session_state(self, filepath: str) -> bool:
        """Save current encryption session state to a file.

        This includes device keys, encryption sessions, and room session keys.

        Args:
            filepath: Path to save the session state

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.client.olm:
                logger.warning(
                    "Encryption not enabled, cannot save session state"
                )
                return False

            session_data = {
                "device_keys": {},
                "olm_sessions": {},
                "megolm_sessions": {},
                "verified_devices": [],
            }

            # Save device keys
            if (
                hasattr(self.client, "device_store")
                and self.client.device_store
            ):
                for user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    session_data["device_keys"][user_id] = {}
                    for device_id, device in user_devices.items():
                        session_data["device_keys"][user_id][device_id] = {
                            "ed25519": getattr(device, "ed25519", None),
                            "curve25519": getattr(device, "curve25519", None),
                            "verified": getattr(device, "verified", False),
                            "display_name": getattr(
                                device, "display_name", None
                            ),
                        }

            # Save encryption sessions
            if hasattr(self.client.olm, "session_store"):
                # This is a simplified representation - actual Olm sessions are complex
                session_data["olm_sessions"] = (
                    "Olm sessions stored in client store"
                )

            # Save verified devices list
            verified_devices = await self.get_verified_devices()
            session_data["verified_devices"] = [
                {"user_id": d["user_id"], "device_id": d["device_id"]}
                for d in verified_devices
            ]

            # Save room sessions (room keys)
            if hasattr(self.client, "store") and self.client.store:
                session_data["megolm_sessions"] = (
                    "Megolm sessions stored in client store"
                )

            import json

            with open(filepath, "w") as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Session state saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return False

    async def load_session_state(self, filepath: str) -> bool:
        """Load encryption session state from a file.

        This restores device verification status and other session data.

        Args:
            filepath: Path to load the session state from

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            import json

            with open(filepath, "r") as f:
                session_data = json.load(f)

            # Restore verified devices
            if "verified_devices" in session_data:
                for device_info in session_data["verified_devices"]:
                    user_id = device_info["user_id"]
                    device_id = device_info["device_id"]

                    # Find the device in the current store
                    if (
                        hasattr(self.client, "device_store")
                        and self.client.device_store
                        and user_id in self.client.device_store.users
                    ):

                        user_devices = self.client.device_store[user_id]
                        if device_id in user_devices:
                            device = user_devices[device_id]
                            # Mark as verified
                            self.client.verify_device(device)
                            logger.info(
                                f"Restored verification for {user_id} device {device_id}"
                            )

            logger.info(f"Session state loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load session state: {e}")
            return False
