"""Main bot implementation with Matrix client.

This module was developed with significant assistance from AI/LLM tools including
GitHub Copilot. The implementation follows Matrix protocol specifications and
uses matrix-nio for client functionality.
"""

import logging
import asyncio
import os
import time
import aiohttp
from typing import Optional, Dict, Any
from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
    InviteMemberEvent,
    MegolmEvent,
    LoginResponse,
    LoginInfoResponse,
    SyncResponse,
    KeyVerificationStart,
    KeyVerificationCancel,
    KeyVerificationKey,
    KeyVerificationMac,
    Event,
)
from chatrixcd.config import Config
from chatrixcd.auth import MatrixAuth
from chatrixcd.semaphore import SemaphoreClient
from chatrixcd.commands import CommandHandler
from chatrixcd.verification import DeviceVerificationManager

logger = logging.getLogger(__name__)


class ChatrixBot:
    """ChatrixCD bot for Matrix with Semaphore UI integration."""

    def __init__(self, config: Config, mode: str = 'tui'):
        """Initialize the bot.
        
        Args:
            config: Bot configuration object
            mode: Operating mode ('tui', 'log', or 'daemon')
        """
        self.config = config
        self.mode = mode  # 'tui', 'log', or 'daemon'
        matrix_config = config.get_matrix_config()
        
        # Initialize Matrix client
        self.homeserver = matrix_config.get('homeserver')
        self.user_id = matrix_config.get('user_id')
        self.device_id = matrix_config.get('device_id')
        self.device_name = matrix_config.get('device_name')
        self.store_path = matrix_config.get('store_path')
        
        # Create store directory if it doesn't exist
        os.makedirs(self.store_path, exist_ok=True)
        
        self.client = AsyncClient(
            homeserver=self.homeserver,
            user=self.user_id,
            device_id=self.device_id,
            store_path=self.store_path,
        )
        
        # Explicitly set user_id on the client to ensure it's available for load_store()
        # In matrix-nio 0.25.x, user_id is not automatically populated from the user parameter
        self.client.user_id = self.user_id
        
        # Initialize authentication handler
        self.auth = MatrixAuth(matrix_config)
        
        # Initialize Semaphore client
        semaphore_config = config.get_semaphore_config()
        self.semaphore = SemaphoreClient(
            url=semaphore_config.get('url'),
            api_token=semaphore_config.get('api_token'),
            ssl_verify=semaphore_config.get('ssl_verify', True),
            ssl_ca_cert=semaphore_config.get('ssl_ca_cert'),
            ssl_client_cert=semaphore_config.get('ssl_client_cert'),
            ssl_client_key=semaphore_config.get('ssl_client_key')
        )
        
        # Initialize command handler
        self.command_handler = CommandHandler(
            bot=self,
            config=config.get_bot_config(),
            semaphore=self.semaphore
        )
        
        # Initialize verification manager
        self.verification_manager = DeviceVerificationManager(self.client)
        
        # Track session IDs for which we've already requested keys
        # This prevents duplicate key requests
        self.requested_session_ids = set()
        
        # Track bot start time to ignore old messages
        # Using milliseconds since epoch to match Matrix server_timestamp format
        self.start_time = int(time.time() * 1000)
        
        # Track whether we've done initial encryption setup after first sync
        self._encryption_setup_done = False
        
        # Setup event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.invite_callback, InviteMemberEvent)
        self.client.add_event_callback(self.megolm_event_callback, MegolmEvent)
        self.client.add_event_callback(self.reaction_callback, Event)
        
        # Setup key verification callbacks for interactive emoji verification
        self.client.add_event_callback(self.key_verification_start_callback, KeyVerificationStart)
        self.client.add_event_callback(self.key_verification_cancel_callback, KeyVerificationCancel)
        self.client.add_event_callback(self.key_verification_key_callback, KeyVerificationKey)
        self.client.add_event_callback(self.key_verification_mac_callback, KeyVerificationMac)

    async def setup_encryption(self) -> bool:
        """Setup encryption keys after successful login.
        
        This uploads device keys and one-time keys if needed, and queries
        device keys from other users to establish encryption sessions.
        
        Returns:
            True if setup successful, False otherwise
        """
        if not self.client.olm:
            logger.warning("Encryption not enabled, skipping encryption setup")
            return True
            
        try:
            # Upload encryption keys if needed
            if self.client.should_upload_keys:
                logger.info("Uploading encryption keys...")
                response = await self.client.keys_upload()
                if hasattr(response, 'one_time_key_counts'):
                    logger.info(f"Uploaded keys. One-time key counts: {response.one_time_key_counts}")
                else:
                    logger.info("Uploaded encryption keys")
            
            # Query device keys for users we share rooms with
            if self.client.should_query_keys:
                logger.info("Querying device keys for room members...")
                response = await self.client.keys_query()
                logger.info(f"Device key query completed")
            
            return True
            
        except Exception as e:
            logger.error(f"Encryption setup error: {e}")
            return False

    def _get_session_file(self) -> str:
        """Get path to session file for storing access tokens.
        
        Returns:
            Path to session file
        """
        return os.path.join(self.store_path, 'session.json')
    
    def _save_session(self, access_token: str, device_id: str):
        """Save session data to file for restoration.
        
        Args:
            access_token: The access token from login
            device_id: The device ID from login
        """
        import json
        session_file = self._get_session_file()
        
        try:
            session_data = {
                'user_id': self.user_id,
                'device_id': device_id,
                'access_token': access_token,
                'homeserver': self.homeserver
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
            
            # Set restrictive permissions on session file (readable only by owner)
            os.chmod(session_file, 0o600)
            logger.info(f"Session saved to {session_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
    
    def _load_session(self) -> Optional[Dict[str, str]]:
        """Load saved session data from file.
        
        Returns:
            Session data dict or None if not available
        """
        import json
        session_file = self._get_session_file()
        
        if not os.path.exists(session_file):
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Validate session data
            required_keys = ['user_id', 'device_id', 'access_token', 'homeserver']
            if all(key in session_data for key in required_keys):
                # Check if session matches current configuration
                if (session_data['user_id'] == self.user_id and 
                    session_data['homeserver'] == self.homeserver):
                    logger.info("Found saved session, attempting to restore")
                    return session_data
                else:
                    logger.info("Saved session is for different user/homeserver, ignoring")
                    return None
            else:
                logger.warning("Saved session data is invalid")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return None
    
    async def login(self, oidc_token_callback=None) -> bool:
        """Login to Matrix server using configured authentication method.
        
        Supports two authentication methods:
        1. Password authentication: Direct login with username/password
        2. OIDC authentication: Interactive SSO login with browser callback
        
        For OIDC, if a valid session is saved, it will be restored automatically
        without requiring interactive login.
        
        Args:
            oidc_token_callback: Optional async callback for OIDC token input.
                               Useful for TUI integration. Should accept
                               (sso_url, redirect_url, identity_providers)
                               and return the login token.
        
        Returns:
            True if login successful, False otherwise
        """
        # Validate that user_id is set for all authentication types
        if not self.user_id:
            logger.error("user_id is not set in configuration. Please add 'user_id' to config.json")
            return False
        
        # Load existing encryption store if it exists
        # This must be done before login to restore device keys
        if self.client.olm:
            try:
                logger.info("Loading encryption store...")
                self.client.load_store()
                logger.info("Encryption store loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load encryption store (this is normal on first run): {e}")
        
        # Validate authentication configuration
        is_valid, error_msg = self.auth.validate_config()
        if not is_valid:
            logger.error(f"Authentication configuration error: {error_msg}")
            return False
        
        auth_type = self.auth.get_auth_type()
        
        try:
            if auth_type == 'password':
                # Password authentication using matrix-nio
                password = self.auth.get_password()
                
                logger.info(f"Logging in with password authentication as {self.user_id}")
                response = await self.client.login(
                    password=password,
                    device_name=self.device_name
                )
                
                if isinstance(response, LoginResponse):
                    logger.info(f"Successfully logged in as {self.user_id}")
                    # Save session for future use
                    self._save_session(response.access_token, response.device_id)
                    # Setup encryption keys after successful login
                    await self.setup_encryption()
                    return True
                else:
                    logger.error(f"Password login failed: {response}")
                    return False
                    
            elif auth_type == 'oidc':
                # Try to restore saved session first
                session_data = self._load_session()
                if session_data:
                    try:
                        logger.info("Attempting to restore saved session...")
                        self.client.restore_login(
                            user_id=session_data['user_id'],
                            device_id=session_data['device_id'],
                            access_token=session_data['access_token']
                        )
                        
                        # Load encryption store after restoring session
                        if self.client.olm:
                            try:
                                logger.info("Loading encryption store after session restore...")
                                self.client.load_store()
                                logger.info("Encryption store loaded successfully after restore")
                            except Exception as e:
                                logger.warning(f"Could not load encryption store after restore (this is normal on first run): {e}")
                        
                        # Test the restored session with a sync
                        sync_response = await self.client.sync(timeout=5000)
                        if hasattr(sync_response, 'rooms'):
                            logger.info("Successfully restored session from saved data")
                            await self.setup_encryption()
                            return True
                        else:
                            logger.warning(f"Restored session test failed: {sync_response}")
                            # Fall through to interactive OIDC login
                            
                    except Exception as e:
                        logger.warning(f"Failed to restore session: {e}")
                        # Fall through to interactive OIDC login
                
                # OIDC authentication using Matrix SSO flow
                return await self._login_oidc(token_callback=oidc_token_callback)
            else:
                logger.error(f"Unknown auth_type: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def _get_oidc_identity_providers(self) -> list:
        """Get list of identity providers from the Matrix server.
        
        Returns:
            List of identity provider dictionaries with 'id', 'name', 'icon', 'brand'
        """
        identity_providers = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.homeserver}/_matrix/client/v3/login") as resp:
                    if resp.status == 200:
                        response_data = await resp.json()
                        flows = response_data.get('flows', [])
                        
                        for flow in flows:
                            if flow.get('type') == 'm.login.sso':
                                identity_providers = flow.get('identity_providers', [])
                                break
                        
                        logger.debug(f"Found {len(identity_providers)} identity providers")
                    else:
                        logger.warning(f"Failed to get login flows: HTTP {resp.status}")
        except Exception as e:
            logger.warning(f"Failed to fetch identity providers: {e}")
        
        return identity_providers

    async def _build_oidc_redirect_url(self, identity_providers: list) -> tuple:
        """Build SSO redirect URL based on available identity providers.
        
        Args:
            identity_providers: List of available identity providers
            
        Returns:
            Tuple of (sso_redirect_url, redirect_url)
        """
        redirect_url = self.auth.get_oidc_redirect_url()
        
        if identity_providers and len(identity_providers) == 1:
            # Single provider - use specific provider URL
            provider_id = identity_providers[0].get('id')
            sso_redirect_url = (
                f"{self.homeserver}/_matrix/client/v3/login/sso/redirect/{provider_id}"
                f"?redirectUrl={redirect_url}"
            )
            logger.info(f"Using identity provider: {identity_providers[0].get('name', provider_id)}")
        else:
            # Multiple or no providers - use generic SSO URL
            sso_redirect_url = (
                f"{self.homeserver}/_matrix/client/v3/login/sso/redirect"
                f"?redirectUrl={redirect_url}"
            )
            
            if identity_providers and len(identity_providers) > 1:
                logger.info(f"Multiple identity providers available ({len(identity_providers)})")
        
        logger.debug(f"SSO redirect URL: {sso_redirect_url}")
        return sso_redirect_url, redirect_url

    async def _get_oidc_token_from_user(self, sso_redirect_url: str, redirect_url: str, 
                                        identity_providers: list, token_callback=None) -> str:
        """Get OIDC login token from user after browser authentication.
        
        Args:
            sso_redirect_url: URL for user to visit
            redirect_url: Redirect URL after authentication
            identity_providers: List of available providers
            token_callback: Optional callback function to display URL and get token
            
        Returns:
            Login token string, or None if failed
        """
        if token_callback:
            # Use provided callback (e.g., from TUI)
            try:
                login_token = await token_callback(sso_redirect_url, redirect_url, identity_providers)
                if not login_token:
                    logger.error("No login token provided by callback")
                    return None
            except Exception as e:
                logger.error(f"Token callback failed: {e}")
                return None
        else:
            # Default: Display instructions and wait for console input
            logger.info("=" * 70)
            logger.info("OIDC Authentication Required")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Please complete the following steps:")
            logger.info("1. Open this URL in your browser:")
            logger.info(f"   {sso_redirect_url}")
            logger.info("")
            logger.info("2. Log in with your credentials")
            logger.info("")
            logger.info("3. After successful login, you'll be redirected to:")
            logger.info(f"   {redirect_url}?loginToken=...")
            logger.info("")
            logger.info("4. Copy the 'loginToken' value from the URL")
            logger.info("")
            
            if identity_providers and len(identity_providers) > 1:
                logger.info("Available Identity Providers:")
                for i, idp in enumerate(identity_providers, 1):
                    logger.info(f"   {i}. {idp.get('name', idp.get('id', 'Unknown'))}")
                logger.info("")
            
            logger.info("=" * 70)
            login_token = input("Enter loginToken: ").strip()
            
            if not login_token:
                logger.error("No login token provided")
                return None
        
        return login_token

    async def _login_oidc(self, token_callback=None) -> bool:
        """Perform OIDC authentication using Matrix SSO flow.
        
        Args:
            token_callback: Optional callback to retrieve login token
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Step 1: Get available login flows from server
            logger.info("Querying server for available login flows...")
            login_info = await self.client.login_info()
            
            if not isinstance(login_info, LoginInfoResponse):
                logger.error(f"Failed to get login info: {login_info}")
                return False
            
            # Check if SSO login is supported
            if 'm.login.sso' not in login_info.flows and 'm.login.token' not in login_info.flows:
                logger.error(
                    "Server does not support SSO/OIDC login. "
                    f"Available flows: {login_info.flows}"
                )
                return False
            
            logger.info("Server supports SSO login")
            
            # Step 2: Get identity providers and build redirect URL
            identity_providers = await self._get_oidc_identity_providers()
            sso_redirect_url, redirect_url = await self._build_oidc_redirect_url(identity_providers)
            
            # Step 3: Get login token from user
            login_token = await self._get_oidc_token_from_user(
                sso_redirect_url, redirect_url, identity_providers, token_callback
            )
            
            if not login_token:
                return False
            
            # Step 4: Complete login with token
            logger.info("Attempting login with provided token...")
            response = await self.client.login(
                token=login_token,
                device_name=self.device_name
            )
            
            if isinstance(response, LoginResponse):
                logger.info(f"Successfully logged in as {self.user_id} via OIDC")
                self._save_session(response.access_token, response.device_id)
                await self.setup_encryption()
                return True
            else:
                # Provide helpful error message
                error_msg = str(response)
                if "Invalid login token" in error_msg or "M_FORBIDDEN" in error_msg:
                    logger.error(
                        f"OIDC login failed: {response}\n"
                        "The login token is invalid or has expired. This can happen if:\n"
                        "  1. The token was copied incorrectly\n"
                        "  2. Too much time has passed since authentication\n"
                        "  3. The token was already used\n"
                        "Please try the OIDC login process again."
                    )
                else:
                    logger.error(f"OIDC login failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"OIDC login error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages.
        
        Args:
            room: The room the message was sent in
            event: The message event
        """
        # Ignore messages from the bot itself
        if event.sender == self.user_id:
            return
        
        # Ignore old messages that were sent before the bot started
        # This prevents processing a backlog of messages on reconnect
        if event.server_timestamp < self.start_time:
            logger.debug(
                f"Ignoring old message from {event.sender} in {room.display_name} "
                f"(message timestamp: {event.server_timestamp}, bot start time: {self.start_time})"
            )
            return
        
        logger.info(f"Message from {event.sender} in {room.display_name}: {event.body}")
        
        # Check if message is a command
        await self.command_handler.handle_message(room, event)

    async def invite_callback(self, room: MatrixRoom, event: InviteMemberEvent):
        """Handle room invites.
        
        Args:
            room: The room we were invited to
            event: The invite event
        """
        logger.info(f"Invited to room {room.room_id} by {event.sender}")
        
        # Auto-join all rooms for now (could add whitelist later)
        await self.client.join(room.room_id)
        logger.info(f"Joined room {room.room_id}")

    async def megolm_event_callback(self, room: MatrixRoom, event: MegolmEvent):
        """Handle Megolm encrypted messages.
        
        This callback is triggered for all encrypted messages (MegolmEvent).
        If the message was successfully decrypted, it will be processed as a normal message.
        If decryption failed, it will actively work to establish proper encryption and request the key.
        In daemon/log modes, it will also attempt automatic verification of unverified devices.
        
        Args:
            room: The room the encrypted message was sent in
            event: The Megolm event (may be decrypted or undecrypted)
        """
        # Check if the message was successfully decrypted
        if event.decrypted:
            # Message was successfully decrypted
            decrypted_event = event.decrypted
            
            # Check if the decrypted event is a text message
            if isinstance(decrypted_event, RoomMessageText):
                logger.debug(
                    f"Processing decrypted message from {event.sender} in {room.display_name}"
                )
                
                # Copy server_timestamp from the MegolmEvent to the decrypted event
                # The decrypted event might not have this attribute set properly,
                # so we ensure it has the correct timestamp for filtering old messages
                if not hasattr(decrypted_event, 'server_timestamp'):
                    decrypted_event.server_timestamp = event.server_timestamp
                
                # Process the decrypted message using the regular message callback
                await self.message_callback(room, decrypted_event)
            else:
                logger.debug(
                    f"Decrypted event from {event.sender} in {room.display_name} "
                    f"is not a text message (type: {type(decrypted_event).__name__})"
                )
            return
        
        # Message couldn't be decrypted - actively work to fix this
        logger.warning(
            f"Unable to decrypt message in {room.display_name} ({room.room_id}) "
            f"from {event.sender}. Taking steps to establish encryption..."
        )
        
        # Check if encryption store is loaded before trying to request keys
        if not self.client.store or not self.client.olm:
            logger.error(
                "Cannot establish encryption: encryption store is not loaded. "
                "Make sure user_id is set correctly and the bot has logged in with encryption support."
            )
            return
        
        # Step 1: Query device keys for the sender to ensure we have up-to-date device information
        try:
            logger.info(f"Querying device keys for {event.sender} to establish encryption")
            if self.client.olm:
                self.client.olm.users_for_key_query.add(event.sender)
            await self.client.keys_query()
            logger.debug(f"Device keys queried successfully for {event.sender}")
        except Exception as e:
            logger.error(f"Failed to query device keys for {event.sender}: {e}")
        
        # Step 2: Try to claim one-time keys and establish encryption sessions with sender's devices
        try:
            if hasattr(self.client, 'device_store') and self.client.device_store:
                if event.sender in self.client.device_store.users:
                    sender_devices = self.client.device_store[event.sender]
                    
                    # Claim one-time keys for devices we don't have sessions with
                    devices_to_claim = {}
                    for device_id, device in sender_devices.items():
                        # Check if we already have an encryption session with this device
                        if not self.client.olm.session_store.get(device.curve25519):
                            devices_to_claim[event.sender] = [device_id]
                            logger.info(
                                f"Need to establish encryption session with {event.sender}'s device {device_id}"
                            )
                    
                    # Claim keys if needed
                    if devices_to_claim:
                        logger.info("Claiming one-time keys to establish encryption sessions")
                        response = await self.client.keys_claim(devices_to_claim)
                        if hasattr(response, 'one_time_keys'):
                            logger.info(
                                f"Successfully claimed one-time keys and established encryption sessions "
                                f"with {len(response.one_time_keys)} device(s)"
                            )
                        else:
                            logger.warning(f"Keys claim returned unexpected response: {response}")
        except Exception as e:
            logger.error(f"Failed to claim one-time keys for {event.sender}: {e}")
        
        # Step 3: In daemon/log modes, automatically verify unverified devices to enable communication
        if self.mode in ['daemon', 'log']:
            try:
                await self._auto_verify_sender_devices(event.sender)
            except Exception as e:
                logger.error(f"Failed to auto-verify devices for {event.sender}: {e}")
        
        # Step 4: Request the room key from the sender
        # Check if we've already requested this session key to avoid duplicate requests
        session_key = f"{event.sender}:{event.session_id}"
        if session_key in self.requested_session_ids:
            logger.debug(
                f"Already requested key for session {event.session_id} from {event.sender}, "
                "skipping duplicate request"
            )
            return
        
        try:
            # Track that we're requesting this session ID from this sender BEFORE making the request
            # This prevents race conditions if the same event is processed multiple times
            self.requested_session_ids.add(session_key)
            
            # Request the room key from other devices
            logger.info(f"Requesting room key for session {event.session_id} from {event.sender}")
            await self.client.request_room_key(event)
            
            # Send the to-device messages to actually deliver the request
            await self.client.send_to_device_messages()
            
            logger.info(
                f"Sent room key request for session {event.session_id} to {event.sender}. "
                "Waiting for key to be shared..."
            )
        except Exception as e:
            error_msg = str(e)
            # matrix-nio prevents duplicate key requests internally
            # If we get this error, it means nio already requested the key, which is fine
            if "key sharing request is already sent out" in error_msg.lower():
                logger.debug(
                    f"Key request for session {event.session_id} already in progress "
                    f"(managed by matrix-nio). This is normal behavior."
                )
            else:
                # For other errors, log as error and remove from tracking so we can retry
                logger.error(f"Failed to request room key: {e}")
                self.requested_session_ids.discard(session_key)

    async def _auto_verify_sender_devices(self, sender: str):
        """Automatically verify all unverified devices for a sender in daemon/log modes.
        
        This enables the bot to communicate with users in encrypted rooms by automatically
        trusting their devices without requiring interactive verification.
        
        Args:
            sender: User ID whose devices should be auto-verified
        """
        if not self.client.olm or not hasattr(self.client, 'device_store') or not self.client.device_store:
            return
        
        # Get unverified devices for this sender
        unverified_devices = []
        if sender in self.client.device_store.users:
            sender_devices = self.client.device_store[sender]
            for _, device in sender_devices.items():
                if not getattr(device, 'verified', False):
                    unverified_devices.append(device)
        
        if not unverified_devices:
            logger.debug(f"No unverified devices found for {sender}")
            return
        
        logger.info(f"Auto-verifying {len(unverified_devices)} device(s) for {sender}")
        
        # Auto-verify each device
        for device in unverified_devices:
            try:
                # Mark device as verified in the store
                self.client.verify_device(device)
                logger.info(f"Auto-verified device {device.id} for user {sender}")
                
                # Share room keys with the newly verified device
                await self.verification_manager._share_room_keys_with_device(device)
                
            except Exception as e:
                logger.error(f"Failed to auto-verify device {device.id} for {sender}: {e}")

    async def reaction_callback(self, room: MatrixRoom, event: Event):
        """Handle incoming reactions.
        
        Args:
            room: The room the reaction was sent in
            event: The reaction event
        """
        # Check if this is a reaction event
        if not hasattr(event, 'source') or 'content' not in event.source:
            return
            
        content = event.source.get('content', {})
        relates_to = content.get('m.relates_to', {})
        
        # Check if this is an annotation (reaction)
        if relates_to.get('rel_type') != 'm.annotation':
            return
        
        # Ignore reactions from the bot itself
        if event.sender == self.user_id:
            return
        
        # Ignore old reactions
        if event.server_timestamp < self.start_time:
            return
        
        # Get the reaction key (emoji) and the event being reacted to
        reaction_key = relates_to.get('key')
        reacted_event_id = relates_to.get('event_id')
        
        if not reaction_key or not reacted_event_id:
            return
        
        logger.info(f"Reaction {reaction_key} from {event.sender} on event {reacted_event_id}")
        
        # Pass the reaction to the command handler
        await self.command_handler.handle_reaction(room, event.sender, reacted_event_id, reaction_key)

    async def send_message(self, room_id: str, message: str, 
                          formatted_message: Optional[str] = None,
                          msgtype: str = "m.text"):
        """Send a message to a room.
        
        Args:
            room_id: ID of the room to send to
            message: Plain text message
            formatted_message: Optional HTML formatted message
            msgtype: Message type - "m.text" for normal messages, "m.notice" for non-urgent notifications
        """
        content = {
            "msgtype": msgtype,
            "body": message,
        }
        
        if formatted_message:
            content["format"] = "org.matrix.custom.html"
            content["formatted_body"] = formatted_message
            
        response = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content=content,
            ignore_unverified_devices=True
        )
        
        # Return the event_id for potential reactions
        if hasattr(response, 'event_id'):
            return response.event_id
        return None

    async def send_reaction(self, room_id: str, event_id: str, emoji: str):
        """Send a reaction to a message.
        
        Args:
            room_id: ID of the room
            event_id: ID of the event to react to
            emoji: Emoji to react with
        """
        try:
            content = {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": event_id,
                    "key": emoji
                }
            }
            
            await self.client.room_send(
                room_id=room_id,
                message_type="m.reaction",
                content=content,
                ignore_unverified_devices=True
            )
        except Exception as e:
            logger.debug(f"Failed to send reaction: {e}")

    async def send_startup_message(self):
        """Send startup message to configured greeting rooms."""
        bot_config = self.config.get_bot_config()
        greetings_enabled = bot_config.get('greetings_enabled', True)
        greeting_rooms = bot_config.get('greeting_rooms', [])
        startup_message = bot_config.get('startup_message', '🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!')
        
        if not greetings_enabled:
            logger.info("Greetings are disabled, skipping startup message")
            return
        
        if not greeting_rooms:
            logger.info("No greeting rooms configured, skipping startup message")
            return
        
        logger.info(f"Sending startup message to {len(greeting_rooms)} room(s)")
        for room_id in greeting_rooms:
            try:
                await self.send_message(room_id, startup_message)
                logger.info(f"Sent startup message to room {room_id}")
            except Exception as e:
                logger.error(f"Failed to send startup message to room {room_id}: {e}")

    async def send_shutdown_message(self):
        """Send shutdown message to configured greeting rooms."""
        bot_config = self.config.get_bot_config()
        greetings_enabled = bot_config.get('greetings_enabled', True)
        greeting_rooms = bot_config.get('greeting_rooms', [])
        shutdown_message = bot_config.get('shutdown_message', '👋 ChatrixCD bot is shutting down. See you later!')
        
        if not greetings_enabled:
            logger.info("Greetings are disabled, skipping shutdown message")
            return
        
        if not greeting_rooms:
            logger.info("No greeting rooms configured, skipping shutdown message")
            return
        
        logger.info(f"Sending shutdown message to {len(greeting_rooms)} room(s)")
        for room_id in greeting_rooms:
            try:
                await self.send_message(room_id, shutdown_message)
                logger.info(f"Sent shutdown message to room {room_id}")
            except Exception as e:
                logger.error(f"Failed to send shutdown message to room {room_id}: {e}")

    async def sync_callback(self, response: SyncResponse):
        """Handle sync responses and manage encryption keys.
        
        This callback is called after each sync to handle encryption-related tasks
        like uploading keys, querying device keys, and claiming one-time keys.
        It also proactively queries device keys for members of encrypted rooms.
        
        Args:
            response: The sync response from the server
        """
        # Handle encryption key management after each sync
        if self.client.olm:
            # Upload keys if needed
            if self.client.should_upload_keys:
                logger.debug("Uploading keys after sync...")
                await self.client.keys_upload()
            
            # Query device keys if needed
            if self.client.should_query_keys:
                logger.debug("Querying device keys after sync...")
                await self.client.keys_query()
            
            # Proactively query device keys for all members of encrypted rooms
            # This ensures we have up-to-date device information for all users we might need to encrypt to
            try:
                if hasattr(response, 'rooms') and hasattr(response.rooms, 'join'):
                    users_to_query = set()
                    encrypted_rooms_count = 0
                    
                    # Collect users from all encrypted rooms
                    for room_id, _ in response.rooms.join.items():
                        # Check if this is an encrypted room
                        room = self.client.rooms.get(room_id)
                        if room and room.encrypted:
                            encrypted_rooms_count += 1
                            # Add all room members to the set of users to query
                            for user_id in room.users:
                                # Skip our own user_id
                                if user_id != self.client.user_id:
                                    users_to_query.add(user_id)
                    
                    # Query device keys for all collected users
                    if users_to_query:
                        # On first sync, log more details
                        if not self._encryption_setup_done:
                            logger.info(
                                f"Initial encryption setup: Found {encrypted_rooms_count} encrypted room(s) "
                                f"with {len(users_to_query)} unique user(s)"
                            )
                            logger.info("Querying device keys for all users in encrypted rooms...")
                            if self.client.olm:
                                self.client.olm.users_for_key_query.update(users_to_query)
                            await self.client.keys_query()
                            
                            # Claim one-time keys to establish Olm sessions with all devices
                            logger.info("Claiming one-time keys to establish Olm sessions...")
                            devices_to_claim = {}
                            if hasattr(self.client, 'device_store') and self.client.device_store:
                                for user_id in users_to_query:
                                    if user_id in self.client.device_store.users:
                                        user_devices = self.client.device_store[user_id]
                                        device_ids = []
                                        for device_id, device in user_devices.items():
                                            # Check if we already have a session
                                            if not self.client.olm.session_store.get(device.curve25519):
                                                device_ids.append(device_id)
                                        
                                        if device_ids:
                                            devices_to_claim[user_id] = device_ids
                            
                            if devices_to_claim:
                                logger.info(
                                    f"Claiming keys for {sum(len(d) for d in devices_to_claim.values())} device(s) "
                                    f"across {len(devices_to_claim)} user(s)"
                                )
                                response = await self.client.keys_claim(devices_to_claim)
                                if hasattr(response, 'one_time_keys'):
                                    logger.info(
                                        f"Successfully established Olm sessions with "
                                        f"{len(response.one_time_keys)} device(s)"
                                    )
                            
                            self._encryption_setup_done = True
                            logger.info("Initial encryption setup completed")
                        else:
                            # Subsequent syncs - just query if there are new users
                            logger.debug(
                                f"Proactively querying device keys for {len(users_to_query)} "
                                f"user(s) in encrypted rooms"
                            )
                            if self.client.olm:
                                self.client.olm.users_for_key_query.update(users_to_query)
                            await self.client.keys_query()
            except Exception as e:
                logger.debug(f"Error during proactive device key query: {e}")

    async def run(self):
        """Run the bot."""
        logger.info("Starting ChatrixCD bot...")
        
        # Start auto-reload for config, aliases, and messages (if not already started)
        if hasattr(self.config, 'start_auto_reload'):
            self.config.start_auto_reload()
        if hasattr(self.command_handler.alias_manager, 'start_auto_reload'):
            self.command_handler.alias_manager.start_auto_reload()
        if hasattr(self.command_handler.message_manager, 'start_auto_reload'):
            self.command_handler.message_manager.start_auto_reload()
        
        # Login
        if not await self.login():
            logger.error("Failed to login, exiting")
            return
        
        # Send startup message
        await self.send_startup_message()
        
        # Register sync callback for encryption key management
        self.client.add_response_callback(self.sync_callback, SyncResponse)
            
        # Start sync loop with retry logic for recoverable errors
        logger.info("Starting sync loop...")
        max_retries = 5
        retry_count = 0
        retry_delay = 5
        
        while retry_count < max_retries:
            try:
                await self.client.sync_forever(timeout=30000, full_state=True)
                # If sync_forever returns normally, break the loop
                break
            except Exception as e:
                error_msg = str(e)
                
                # Handle specific error types
                if "not verified or blacklisted" in error_msg:
                    # This is a non-fatal error related to E2E encryption with unverified devices
                    logger.warning(
                        f"Encryption error: {error_msg}\n"
                        "Note: This error occurs when trying to send encrypted messages to unverified devices. "
                        "The bot will continue operating. To resolve this:\n"
                        "  1. Verify the mentioned device through the TUI (VER menu)\n"
                        "  2. Or ask the user to verify their device\n"
                        "  3. Unverified users can still receive messages in unencrypted rooms"
                    )
                    # Continue running despite this error
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"Retrying sync loop in {retry_delay} seconds... (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        # Exponential backoff
                        retry_delay = min(retry_delay * 2, 60)
                        continue
                    else:
                        logger.error("Max retries reached for sync loop")
                        break
                        
                elif "Invalid login token" in error_msg or "M_FORBIDDEN" in error_msg:
                    # Authentication error - not recoverable
                    logger.error(
                        f"Authentication error: {error_msg}\n"
                        "This error indicates the login credentials are invalid or expired. "
                        "Please check your configuration and try logging in again."
                    )
                    break
                    
                else:
                    # Unknown error - log and retry with backoff
                    logger.error(f"Sync loop error: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"Retrying sync loop in {retry_delay} seconds... (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        # Exponential backoff
                        retry_delay = min(retry_delay * 2, 60)
                        continue
                    else:
                        logger.error("Max retries reached for sync loop")
                        break
        
        # Cleanup
        await self.close()

    async def key_verification_start_callback(self, event: KeyVerificationStart):
        """Handle incoming key verification start events.
        
        This callback is triggered when another device initiates verification with the bot.
        Behavior depends on the bot's operating mode:
        - daemon mode: Automatically accept and verify (no user interaction)
        - log mode: Interactive command-line verification
        - tui mode: Notification shown in TUI for manual verification
        
        Args:
            event: Key verification start event
        """
        logger.info(
            f"Received key verification request from {event.sender} (device: {event.from_device})\n"
            f"Transaction ID: {event.transaction_id}"
        )
        
        if self.mode == 'daemon':
            # In daemon mode, automatically accept and verify all requests
            await self._auto_verify_device(event.transaction_id)
        elif self.mode == 'log':
            # In log-only mode, handle verification interactively on command line
            await self._interactive_cli_verification(event.transaction_id, event.sender, event.from_device)
        else:
            # In TUI mode, just notify (TUI will handle the verification)
            logger.info("To complete this verification, use the TUI (Sessions menu > View Pending Verification Requests)")
    
    async def _auto_verify_device(self, transaction_id: str):
        """Automatically verify a device in daemon mode.
        
        Uses the verification manager to handle auto-verification.
        
        Args:
            transaction_id: Transaction ID of the verification request
        """
        success = await self.verification_manager.auto_verify_pending(transaction_id)
        if success:
            logger.info(f"Successfully auto-verified device in transaction {transaction_id}")
        else:
            logger.warning(f"Failed to auto-verify device in transaction {transaction_id}")
    
    async def _interactive_cli_verification(self, transaction_id: str, sender: str, device_id: str):
        """Handle verification interactively on command line in log-only mode.
        
        Uses the verification manager to handle interactive verification.
        
        Args:
            transaction_id: Transaction ID of the verification request
            sender: User ID of the sender
            device_id: Device ID of the sender
        """
        # Get pending verifications
        pending = await self.verification_manager.get_pending_verifications()
        verification_info = None
        
        for pending_item in pending:
            if pending_item['transaction_id'] == transaction_id:
                verification_info = pending_item
                break
        
        if not verification_info:
            logger.warning(f"Cannot verify: verification {transaction_id} not found")
            return
        
        # Define callback to display emojis and get user confirmation
        async def emoji_callback(emoji_list):
            # Display emojis
            print("\n" + "=" * 70)
            print("VERIFICATION REQUEST")
            print("=" * 70)
            print(f"From: {sender}")
            print(f"Device: {device_id}")
            print("\nCompare these emojis with the other device:")
            print()
            for emoji, desc in emoji_list:
                print(f"  {emoji}  {desc}")
            print()
            print("=" * 70)
            
            # Prompt user
            response = input("Do the emojis match? (yes/no): ").strip().lower()
            
            if response in ('yes', 'y'):
                logger.info("✅ Device verified successfully")
                print("✅ Device verified and marked as trusted")
                return True
            else:
                logger.info("❌ Verification rejected")
                print("❌ Verification rejected - emojis did not match")
                return False
        
        # Verify using the verification manager
        success = await self.verification_manager.verify_pending_interactive(
            verification_info, emoji_callback
        )
        
        if not success:
            logger.error("Failed to complete interactive verification")
            print("Failed to complete verification. See logs for details.")
        
    async def key_verification_cancel_callback(self, event: KeyVerificationCancel):
        """Handle key verification cancellation events.
        
        Args:
            event: Key verification cancel event
        """
        logger.info(
            f"Key verification cancelled by {event.sender}\n"
            f"Reason: {event.reason}\n"
            f"This is normal if the verification timed out or was explicitly cancelled."
        )
    
    async def key_verification_key_callback(self, event: KeyVerificationKey):
        """Handle key verification key exchange events.
        
        Args:
            event: Key verification key event
        """
        logger.debug(f"Key verification key exchange with {event.sender}")
    
    async def key_verification_mac_callback(self, event: KeyVerificationMac):
        """Handle key verification MAC events.
        
        Args:
            event: Key verification MAC event
        """
        logger.debug(f"Key verification MAC received from {event.sender}")

    async def close(self):
        """Clean up resources."""
        logger.info("Shutting down bot...")
        
        # Send shutdown message before closing
        await self.send_shutdown_message()
        
        await self.semaphore.close()
        await self.client.close()
