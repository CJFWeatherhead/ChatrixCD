"""Tests for bot module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
import os
import tempfile
from nio import MegolmEvent, MatrixRoom, RoomMessageText
from chatrixcd.bot import ChatrixBot
from chatrixcd.config import Config


class TestChatrixBot(unittest.TestCase):
    """Test ChatrixBot class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create temporary directory for store
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration
        self.config = MagicMock(spec=Config)
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.com',
            'user_id': '@bot:example.com',
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'password',
            'password': 'testpass'
        }
        self.config.get_semaphore_config.return_value = {
            'url': 'https://semaphore.example.com',
            'api_token': 'test_token'
        }
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': []
        }

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.loop.close()

    def test_init_registers_callbacks(self):
        """Test that bot initialization registers event callbacks."""
        bot = ChatrixBot(self.config)
        
        # Verify callbacks are registered
        callbacks = bot.client.event_callbacks
        
        # Check that we have callbacks for the right event types
        from nio import RoomMessageText, InviteMemberEvent, MegolmEvent
        
        # Find callbacks for each event type
        # Each callback is a ClientCallback object with a 'filter' attribute
        has_message_callback = any(
            cb.filter == RoomMessageText
            for cb in callbacks
        )
        has_invite_callback = any(
            cb.filter == InviteMemberEvent
            for cb in callbacks
        )
        has_megolm_callback = any(
            cb.filter == MegolmEvent
            for cb in callbacks
        )
        
        self.assertTrue(has_message_callback, "RoomMessageText callback not registered")
        self.assertTrue(has_invite_callback, "InviteMemberEvent callback not registered")
        self.assertTrue(has_megolm_callback, "MegolmEvent callback not registered")

    def test_decryption_failure_callback(self):
        """Test that decryption failure callback requests room keys."""
        bot = ChatrixBot(self.config)
        
        # Mock the request_room_key method
        bot.client.request_room_key = AsyncMock()
        
        # Create mock room and event
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        event = MagicMock(spec=MegolmEvent)
        event.sender = "@user:example.com"
        event.session_id = "test_session_id"
        
        # Call the callback
        self.loop.run_until_complete(
            bot.decryption_failure_callback(room, event)
        )
        
        # Verify request_room_key was called
        bot.client.request_room_key.assert_called_once_with(event)

    def test_message_callback_ignores_own_messages(self):
        """Test that message callback ignores messages from the bot itself."""
        bot = ChatrixBot(self.config)
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room and event from the bot itself
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        
        event = MagicMock(spec=RoomMessageText)
        event.sender = bot.user_id  # Message from bot itself
        event.body = "!cd help"
        
        # Call the callback
        self.loop.run_until_complete(
            bot.message_callback(room, event)
        )
        
        # Verify handle_message was NOT called
        bot.command_handler.handle_message.assert_not_called()

    def test_message_callback_processes_other_messages(self):
        """Test that message callback processes messages from other users."""
        bot = ChatrixBot(self.config)
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room and event from another user
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        
        event = MagicMock(spec=RoomMessageText)
        event.sender = "@other:example.com"  # Different user
        event.body = "!cd help"
        
        # Call the callback
        self.loop.run_until_complete(
            bot.message_callback(room, event)
        )
        
        # Verify handle_message WAS called
        bot.command_handler.handle_message.assert_called_once_with(room, event)

    def test_login_token_loads_store(self):
        """Test that token authentication loads the encryption store."""
        # Configure for token authentication
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.com',
            'user_id': '@bot:example.com',
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'token',
            'access_token': 'test_token_12345'
        }
        
        bot = ChatrixBot(self.config)
        
        # Mock the client methods
        bot.client.load_store = AsyncMock()
        bot.client.sync = AsyncMock()
        from nio import SyncResponse
        bot.client.sync.return_value = SyncResponse()
        
        # Mock the auth handler
        bot.auth.get_access_token = AsyncMock(return_value='test_token_12345')
        
        # Call login
        result = self.loop.run_until_complete(bot.login())
        
        # Verify load_store was called before sync
        self.assertTrue(result, "Login should succeed")
        bot.client.load_store.assert_called_once()
        bot.client.sync.assert_called_once()
        
        # Verify access token was set
        self.assertEqual(bot.client.access_token, 'test_token_12345')


if __name__ == '__main__':
    unittest.main()
