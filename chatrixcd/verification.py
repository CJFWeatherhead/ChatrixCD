"""Device verification module for ChatrixCD.

This module provides reusable verification functionality across TUI, CLI, and daemon modes.
It handles SAS (emoji) verification following the Matrix specification for device trust.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from nio import AsyncClient, ToDeviceError
from nio.crypto import Sas, SasState

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
    
    async def get_verified_devices(self) -> List[Dict[str, Any]]:
        """Get list of verified devices.
        
        Returns:
            List of verified device dictionaries with user_id, device_id,
            device_name, trust_state, and device object
        """
        if not self.client.olm:
            logger.warning("Encryption not enabled, cannot get verified devices")
            return []
        
        verified_devices = []
        
        try:
            if hasattr(self.client, 'device_store') and self.client.device_store:
                for user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    for device_id, device in user_devices.items():
                        # Skip our own device
                        if user_id == self.client.user_id and device_id == self.client.device_id:
                            continue
                        # Only include verified devices
                        if getattr(device, 'verified', False):
                            verified_devices.append({
                                'user_id': user_id,
                                'device_id': device_id,
                                'device_name': getattr(device, 'display_name', 'Unknown'),
                                'trust_state': getattr(device, 'trust_state', None),
                                'device': device
                            })
        except Exception as e:
            logger.error(f"Error getting verified devices: {e}")
        
        return verified_devices
    
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
            if hasattr(self.client, 'device_store') and self.client.device_store:
                if user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    if device_id in user_devices:
                        device = user_devices[device_id]
                        return getattr(device, 'verified', False)
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
            logger.warning("Encryption not enabled, cannot get unverified devices")
            return []
        
        unverified_devices = []
        
        try:
            if hasattr(self.client, 'device_store') and self.client.device_store:
                for user_id in self.client.device_store.users:
                    user_devices = self.client.device_store[user_id]
                    for device_id, device in user_devices.items():
                        # Skip our own device
                        if user_id == self.client.user_id and device_id == self.client.device_id:
                            continue
                        # Only include unverified devices
                        if not getattr(device, 'verified', False):
                            unverified_devices.append({
                                'user_id': user_id,
                                'device_id': device_id,
                                'device_name': getattr(device, 'display_name', 'Unknown'),
                                'device': device
                            })
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
        
        if hasattr(self.client, 'key_verifications') and self.client.key_verifications:
            for transaction_id, verification in self.client.key_verifications.items():
                # For Sas verifications, user_id and device_id are in other_olm_device
                if isinstance(verification, Sas):
                    other_device = getattr(verification, 'other_olm_device', None)
                    if other_device:
                        user_id = getattr(other_device, 'user_id', 'Unknown')
                        device_id = getattr(other_device, 'id', 'Unknown')
                    else:
                        user_id = 'Unknown'
                        device_id = 'Unknown'
                else:
                    user_id = getattr(verification, 'user_id', 'Unknown')
                    device_id = getattr(verification, 'device_id', 'Unknown')
                
                pending.append({
                    'transaction_id': transaction_id,
                    'user_id': user_id,
                    'device_id': device_id,
                    'type': type(verification).__name__,
                    'verification': verification
                })
        
        return pending
    
    async def start_verification(self, device: Any) -> Optional[Sas]:
        """Start SAS verification with a device.
        
        Args:
            device: Device object from device_store
            
        Returns:
            SAS verification object if successful, None otherwise
        """
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
            if hasattr(self.client, 'key_verifications'):
                for transaction_id, verification in self.client.key_verifications.items():
                    if isinstance(verification, Sas):
                        if verification.other_olm_device == device:
                            return verification
            
            logger.warning("Verification started, but could not retrieve SAS object")
            return None
            
        except Exception as e:
            logger.error(f"Error starting verification: {e}")
            return None
    
    async def accept_verification(self, sas: Sas) -> bool:
        """Accept a verification request.
        
        Args:
            sas: SAS verification object
            
        Returns:
            True if accepted successfully, False otherwise
        """
        try:
            if not sas.we_started_it and sas.state == SasState.created:
                await self.client.accept_key_verification(sas.transaction_id)
                # Send the accept message to the other device
                await self.client.send_to_device_messages()
                await asyncio.sleep(0.5)
                return True
            return True
        except Exception as e:
            logger.error(f"Error accepting verification: {e}")
            return False
    
    async def wait_for_key_exchange(self, sas: Sas, max_wait: int = 10) -> bool:
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
    
    async def get_emoji_list(self, sas: Sas) -> Optional[List[Tuple[str, str]]]:
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
    
    async def confirm_verification(self, sas: Sas) -> bool:
        """Confirm the SAS verification (emojis match).
        
        This method confirms the verification and persists the device's verified
        status to the store for future sessions.
        
        Args:
            sas: SAS verification object
            
        Returns:
            True if confirmed successfully, False otherwise
        """
        try:
            if not sas.other_key_set:
                logger.error("Cannot confirm verification: Key exchange not complete")
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
            
            logger.info("Verification confirmed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming verification: {e}")
            return False
    
    async def reject_verification(self, sas: Sas) -> bool:
        """Reject the SAS verification (emojis don't match).
        
        Args:
            sas: SAS verification object
            
        Returns:
            True if rejected successfully, False otherwise
        """
        try:
            if not sas.other_key_set:
                logger.error("Cannot reject verification: Key exchange not complete")
                return False
            
            sas.reject_sas()
            await self.client.send_to_device_messages()
            logger.info("Verification rejected")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting verification: {e}")
            return False
    
    async def auto_verify_pending(self, transaction_id: str) -> bool:
        """Automatically verify a pending verification request (daemon mode).
        
        Args:
            transaction_id: Transaction ID of the verification request
            
        Returns:
            True if auto-verified successfully, False otherwise
        """
        try:
            # Get the SAS verification object
            if not hasattr(self.client, 'key_verifications') or transaction_id not in self.client.key_verifications:
                logger.warning(f"Cannot auto-verify: verification {transaction_id} not found")
                return False
            
            sas = self.client.key_verifications[transaction_id]
            
            if not isinstance(sas, Sas):
                logger.warning(f"Cannot auto-verify: {transaction_id} is not a SAS verification")
                return False
            
            # Accept the verification request
            await self.client.accept_key_verification(transaction_id)
            # Send the accept message to the other device
            await self.client.send_to_device_messages()
            logger.info(f"Auto-accepted verification request {transaction_id}")
            
            # Wait for key exchange
            await asyncio.sleep(1)
            
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
                else:
                    logger.info(f"Auto-verified device in transaction {transaction_id}")
                return True
            else:
                logger.warning(f"Cannot auto-verify {transaction_id}: other device key not received")
                return False
        
        except Exception as e:
            logger.error(f"Error during auto-verification: {e}")
            return False
    
    async def verify_device_interactive(
        self,
        device_info: Dict[str, Any],
        emoji_callback: Callable[[List[Tuple[str, str]]], bool]
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
        device = device_info['device']
        
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
            logger.error("Verification timeout: Did not receive other device's key")
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
        emoji_callback: Callable[[List[Tuple[str, str]]], bool]
    ) -> bool:
        """Verify a pending verification request interactively.
        
        Args:
            verification_info: Verification info dictionary with 'verification' key
            emoji_callback: Async callable that displays emojis and returns True if match
            
        Returns:
            True if verified successfully, False otherwise
        """
        verification = verification_info['verification']
        
        if not isinstance(verification, Sas):
            logger.error(f"Unsupported verification type: {verification_info['type']}")
            return False
        
        sas = verification
        
        # Accept if needed
        if not await self.accept_verification(sas):
            logger.error("Failed to accept verification")
            return False
        
        # Wait for key exchange
        if not await self.wait_for_key_exchange(sas):
            logger.error("Verification timeout: Did not receive other device's key")
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
