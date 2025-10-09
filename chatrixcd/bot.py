"""Main bot implementation with Matrix client."""

import logging
import asyncio
import os
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
        
        # Initialize authentication handler
        self.auth = MatrixAuth(matrix_config)
        
        # Initialize Semaphore client
        semaphore_config = config.get_semaphore_config()
        self.semaphore = SemaphoreClient(
            url=semaphore_config.get('url'),
            api_token=semaphore_config.get('api_token')
        )
        
        # Initialize command handler
        self.command_handler = CommandHandler(
            bot=self,
            config=config.get_bot_config(),
            semaphore=self.semaphore
        )
        
        # Setup event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.invite_callback, InviteMemberEvent)
        self.client.add_event_callback(self.decryption_failure_callback, MegolmEvent)

    async def login(self) -> bool:
        """Login to Matrix server.
        
        Returns:
            True if login successful, False otherwise
        """
        matrix_config = self.config.get_matrix_config()
        auth_type = matrix_config.get('auth_type', 'password')
        
        try:
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
                
                # Set the access token directly
                self.client.access_token = access_token
                
                # Verify the token works by doing a sync
                sync_response = await self.client.sync(timeout=30000)
                if isinstance(sync_response, SyncResponse):
                    logger.info(f"Authenticated with token as {self.user_id}")
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
        
        try:
            # Request the room key from other devices
            await self.client.request_room_key(event)
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

    async def run(self):
        """Run the bot."""
        logger.info("Starting ChatrixCD bot...")
        
        # Login
        if not await self.login():
            logger.error("Failed to login, exiting")
            return
            
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
        await self.semaphore.close()
        await self.client.close()
