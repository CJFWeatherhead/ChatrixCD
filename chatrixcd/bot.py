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
    SyncResponse,
    KeyVerificationStart,
    KeyVerificationCancel,
    KeyVerificationKey,
    KeyVerificationMac,
)
from chatrixcd.config import Config
from chatrixcd.auth import MatrixAuth
from chatrixcd.semaphore import SemaphoreClient
from chatrixcd.commands import CommandHandler

logger = logging.getLogger(__name__)


class ChatrixBot:
    """ChatrixCD bot for Matrix with Semaphore UI integration."""

    def __init__(self, config: Config):
        """Initialize the bot.
        
        Args:
            config: Bot configuration object
        """
        self.config = config
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
        
        # Track session IDs for which we've already requested keys
        # This prevents duplicate key requests
        self.requested_session_ids = set()
        
        # Track bot start time to ignore old messages
        # Using milliseconds since epoch to match Matrix server_timestamp format
        self.start_time = int(time.time() * 1000)
        
        # Setup event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.invite_callback, InviteMemberEvent)
        self.client.add_event_callback(self.megolm_event_callback, MegolmEvent)
        
        # Setup key verification callbacks for interactive emoji verification
        self.client.add_event_callback(self.key_verification_start_callback, KeyVerificationStart)
        self.client.add_event_callback(self.key_verification_cancel_callback, KeyVerificationCancel)
        self.client.add_event_callback(self.key_verification_key_callback, KeyVerificationKey)
        self.client.add_event_callback(self.key_verification_mac_callback, KeyVerificationMac)

    async def setup_encryption(self) -> bool:
        """Setup encryption keys after successful login.
        
        This uploads device keys and one-time keys if needed, and queries
        device keys from other users to establish Olm sessions.
        
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

    async def _login_oidc(self, token_callback=None) -> bool:
        """Perform OIDC authentication using Matrix SSO flow.
        
        This method implements the Matrix SSO login flow:
        1. Query server for available login flows
        2. Parse SSO flow and identity providers from server response
        3. Display appropriate SSO redirect URL to user
        4. Wait for user to complete authentication in browser
        5. User provides the login token from callback
        6. Complete login with the token
        
        Args:
            token_callback: Optional async callback function that displays
                          SSO URL and prompts for token. Should accept
                          (sso_url, redirect_url, identity_providers) and
                          return the login token. If None, uses default
                          console input.
        
        Returns:
            True if login successful, False otherwise
        """
        from nio import LoginInfoResponse
        
        try:
            # Get available login flows from the server
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
            
            # Parse identity providers by making a fresh HTTP request
            # We can't use login_info.transport_response.json() because the aiohttp
            # response body has already been consumed by matrix-nio when creating
            # the LoginInfoResponse object. Attempting to read it again would hang.
            identity_providers = []
            
            try:
                # Make a direct request to get the full login response with identity providers
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.homeserver}/_matrix/client/v3/login") as resp:
                        if resp.status == 200:
                            response_data = await resp.json()
                            flows = response_data.get('flows', [])
                            
                            # Find the m.login.sso flow
                            for flow in flows:
                                if flow.get('type') == 'm.login.sso':
                                    identity_providers = flow.get('identity_providers', [])
                                    break
                            
                            if identity_providers:
                                logger.info(f"Found {len(identity_providers)} identity provider(s)")
                                for idp in identity_providers:
                                    logger.info(f"  - {idp.get('name', idp.get('id', 'Unknown'))}")
                        else:
                            logger.warning(f"Failed to fetch login flows: HTTP {resp.status}")
            except Exception as e:
                logger.warning(f"Could not parse identity providers: {e}")
                # Continue anyway with generic SSO URL
            
            # Get redirect URL from config
            redirect_url = self.auth.get_oidc_redirect_url()
            logger.debug(f"OIDC redirect URL: {redirect_url}")
            
            # Construct SSO redirect URL
            # If there are multiple identity providers, we should let the user choose
            # For now, we'll use the generic redirect (works for single or no-preference)
            logger.debug(f"Constructing SSO redirect URL for {len(identity_providers) if identity_providers else 0} identity provider(s)")
            if identity_providers and len(identity_providers) == 1:
                # Single provider - use specific provider URL
                provider_id = identity_providers[0].get('id')
                sso_redirect_url = (
                    f"{self.homeserver}/_matrix/client/v3/login/sso/redirect/{provider_id}"
                    f"?redirectUrl={redirect_url}"
                )
                logger.info(f"Using identity provider: {identity_providers[0].get('name', provider_id)}")
                logger.debug(f"SSO redirect URL: {sso_redirect_url}")
            elif identity_providers and len(identity_providers) > 1:
                # Multiple providers - user needs to choose
                logger.info("=" * 70)
                logger.info("Multiple Identity Providers Available")
                logger.info("=" * 70)
                logger.info("")
                for i, idp in enumerate(identity_providers, 1):
                    logger.info(f"{i}. {idp.get('name', idp.get('id', 'Unknown'))}")
                logger.info("")
                
                # Let user select
                print("Select identity provider (enter number): ", end='')
                try:
                    choice = int(input().strip())
                    if 1 <= choice <= len(identity_providers):
                        selected_idp = identity_providers[choice - 1]
                        provider_id = selected_idp.get('id')
                        sso_redirect_url = (
                            f"{self.homeserver}/_matrix/client/v3/login/sso/redirect/{provider_id}"
                            f"?redirectUrl={redirect_url}"
                        )
                        logger.info(f"Selected: {selected_idp.get('name', provider_id)}")
                    else:
                        logger.error("Invalid selection")
                        return False
                except (ValueError, EOFError):
                    logger.error("Invalid input")
                    return False
            else:
                # No specific providers or generic SSO
                sso_redirect_url = (
                    f"{self.homeserver}/_matrix/client/v3/login/sso/redirect"
                    f"?redirectUrl={redirect_url}"
                )
                logger.debug(f"Using generic SSO redirect URL: {sso_redirect_url}")
            
            # Get login token from user via callback or default method
            logger.debug(f"Requesting login token from user (callback={'provided' if token_callback else 'console'})")
            if token_callback:
                # Use provided callback (e.g., from TUI)
                logger.debug("Invoking token callback for OIDC authentication")
                login_token = await token_callback(sso_redirect_url, redirect_url, identity_providers)
                logger.debug("Token callback returned successfully")
            else:
                # Default console-based prompt
                logger.info("=" * 70)
                logger.info("OIDC Authentication Required")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Please complete authentication in your browser:")
                logger.info("")
                logger.info(f"  {sso_redirect_url}")
                logger.info("")
                logger.info("After authentication, you will be redirected to:")
                logger.info(f"  {redirect_url}")
                logger.info("")
                logger.info("The redirect URL will contain a 'loginToken' parameter.")
                logger.info("Copy the entire URL or just the loginToken value.")
                logger.info("=" * 70)
                
                # Prompt user for the login token
                print("\nWaiting for login token...")
                login_token = input("Paste the callback URL or loginToken: ").strip()
            
            # Extract token if full URL was provided
            if 'loginToken=' in login_token:
                # Parse the token from URL
                import urllib.parse
                parsed = urllib.parse.urlparse(login_token)
                params = urllib.parse.parse_qs(parsed.query)
                if 'loginToken' in params:
                    login_token = params['loginToken'][0]
                else:
                    # Try fragment as some SSO providers use fragments
                    params = urllib.parse.parse_qs(parsed.fragment)
                    if 'loginToken' in params:
                        login_token = params['loginToken'][0]
                    else:
                        logger.error("Could not find loginToken in provided URL")
                        return False
            
            # Login using the token
            logger.info("Attempting login with provided token...")
            response = await self.client.login(
                token=login_token,
                device_name=self.device_name
            )
            
            if isinstance(response, LoginResponse):
                logger.info(f"Successfully logged in as {self.user_id} via OIDC")
                # Save session for future use (avoid interactive login on reconnect)
                self._save_session(response.access_token, response.device_id)
                # Setup encryption keys after successful login
                await self.setup_encryption()
                return True
            else:
                # Provide more helpful error message
                error_msg = str(response)
                if "Invalid login token" in error_msg or "M_FORBIDDEN" in error_msg:
                    logger.error(
                        f"OIDC login failed: {response}\n"
                        "The login token is invalid or has expired. This can happen if:\n"
                        "  1. The token was copied incorrectly\n"
                        "  2. Too much time has passed since you authenticated in the browser\n"
                        "  3. The token has already been used\n"
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
        If decryption failed, it will request the key from other devices in the room.
        
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
                # Process the decrypted message using the regular message callback
                await self.message_callback(room, decrypted_event)
            else:
                logger.debug(
                    f"Decrypted event from {event.sender} in {room.display_name} "
                    f"is not a text message (type: {type(decrypted_event).__name__})"
                )
            return
        
        # Message couldn't be decrypted - request the key
        logger.warning(
            f"Unable to decrypt message in {room.display_name} ({room.room_id}) "
            f"from {event.sender}. Requesting room key..."
        )
        
        # Check if encryption store is loaded before trying to request keys
        if not self.client.store or not self.client.olm:
            logger.error(
                "Cannot request room key: encryption store is not loaded. "
                "Make sure user_id is set correctly and the bot has logged in with encryption support."
            )
            return
        
        # Check if we've already requested this session key to avoid duplicate requests
        if event.session_id in self.requested_session_ids:
            logger.debug(f"Already requested key for session {event.session_id}, skipping duplicate request")
            return
        
        try:
            # Request the room key from other devices
            await self.client.request_room_key(event)
            # Track that we've requested this session ID
            self.requested_session_ids.add(event.session_id)
            logger.info(f"Requested room key for session {event.session_id}")
        except Exception as e:
            logger.error(f"Failed to request room key: {e}")

    async def send_message(self, room_id: str, message: str, 
                          formatted_message: Optional[str] = None):
        """Send a message to a room.
        
        Args:
            room_id: ID of the room to send to
            message: Plain text message
            formatted_message: Optional HTML formatted message
        """
        content = {
            "msgtype": "m.text",
            "body": message,
        }
        
        if formatted_message:
            content["format"] = "org.matrix.custom.html"
            content["formatted_body"] = formatted_message
            
        await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content=content
        )

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

    async def run(self):
        """Run the bot."""
        logger.info("Starting ChatrixCD bot...")
        
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
        
        Args:
            event: Key verification start event
        """
        logger.info(f"Received key verification start from {event.sender} (device: {event.from_device})")
        
        # The verification will be handled by the SAS object in the client
        # TUI will access client.key_verifications to get active verifications
        
    async def key_verification_cancel_callback(self, event: KeyVerificationCancel):
        """Handle key verification cancellation events.
        
        Args:
            event: Key verification cancel event
        """
        logger.info(f"Key verification cancelled by {event.sender}: {event.reason}")
    
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
