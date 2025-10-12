"""Main bot implementation with Matrix client."""

import logging
import asyncio
import os
import time
from typing import Optional, Dict, Any
from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
    InviteMemberEvent,
    MegolmEvent,
    LoginResponse,
    SyncResponse,
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
        self.client.add_event_callback(self.decryption_failure_callback, MegolmEvent)

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

    async def login(self) -> bool:
        """Login to Matrix server.
        
        Returns:
            True if login successful, False otherwise
        """
        matrix_config = self.config.get_matrix_config()
        auth_type = matrix_config.get('auth_type', 'password')
        
        try:
            # Validate that user_id is set for all authentication types
            if not self.user_id:
                logger.error("user_id is not set in configuration. Please add 'user_id' to config.json")
                return False
            
            if auth_type == 'password':
                # Traditional password login
                password = matrix_config.get('password')
                if not password:
                    logger.error("Password authentication requires password")
                    return False
                    
                response = await self.client.login(
                    password=password,
                    device_name=self.device_name
                )
                
                if isinstance(response, LoginResponse):
                    logger.info(f"Logged in as {self.user_id}")
                    # Setup encryption keys after successful login
                    await self.setup_encryption()
                    return True
                else:
                    logger.error(f"Login failed: {response}")
                    return False
                    
            elif auth_type in ('token', 'oidc'):
                # Token-based or OIDC authentication
                access_token = await self.auth.get_access_token()
                if not access_token:
                    logger.error("Failed to get access token")
                    return False
                
                # Load the encryption store before setting token
                # This is required for E2E encryption to work
                # Note: load_store() requires user_id to be set, which we validated above
                self.client.load_store()
                logger.info("Loaded encryption store")
                
                # Set the access token directly
                self.client.access_token = access_token
                
                # Verify the token works by doing a sync
                sync_response = await self.client.sync(timeout=30000)
                if isinstance(sync_response, SyncResponse):
                    logger.info(f"Authenticated with token as {self.user_id}")
                    # Setup encryption keys after successful authentication
                    await self.setup_encryption()
                    return True
                else:
                    logger.error(f"Token authentication failed: {sync_response}")
                    return False
            else:
                logger.error(f"Unknown auth_type: {auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
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

    async def decryption_failure_callback(self, room: MatrixRoom, event: MegolmEvent):
        """Handle encrypted messages that couldn't be decrypted.
        
        This callback is triggered when the bot receives an encrypted message
        but doesn't have the decryption key. It will request the key from
        other devices in the room.
        
        Args:
            room: The room the encrypted message was sent in
            event: The undecrypted Megolm event
        """
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
            
        # Start sync loop
        logger.info("Starting sync loop...")
        try:
            await self.client.sync_forever(timeout=30000, full_state=True)
        except Exception as e:
            logger.error(f"Sync loop error: {e}")
        finally:
            await self.close()

    async def close(self):
        """Clean up resources."""
        logger.info("Shutting down bot...")
        
        # Send shutdown message before closing
        await self.send_shutdown_message()
        
        await self.semaphore.close()
        await self.client.close()
