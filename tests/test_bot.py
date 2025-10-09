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

    def test_init_sets_client_user_id(self):
        """Test that bot initialization sets client.user_id from config."""
        bot = ChatrixBot(self.config)
        
        # Verify that both bot.user_id and client.user_id are set
        self.assertEqual(bot.user_id, '@bot:example.com')
        self.assertEqual(bot.client.user_id, '@bot:example.com')
        self.assertEqual(bot.client.user, '@bot:example.com')
        
        # Ensure user_id is not empty (important for load_store())
        self.assertTrue(bot.client.user_id)
    
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
        
        # Mock the request_room_key method and store/olm
        bot.client.request_room_key = AsyncMock()
        bot.client.store = MagicMock()  # Mock store to simulate it's loaded
        bot.client.olm = MagicMock()    # Mock olm to simulate it's loaded
        
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

    def test_decryption_failure_callback_without_store(self):
        """Test that decryption failure callback handles missing store gracefully."""
        bot = ChatrixBot(self.config)
        
        # Mock the request_room_key method
        bot.client.request_room_key = AsyncMock()
        
        # Simulate store not loaded (store and olm are None)
        bot.client.store = None
        bot.client.olm = None
        
        # Create mock room and event
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        event = MagicMock(spec=MegolmEvent)
        event.sender = "@user:example.com"
        event.session_id = "test_session_id"
        
        # Call the callback - should not raise an exception
        self.loop.run_until_complete(
            bot.decryption_failure_callback(room, event)
        )
        
        # Verify request_room_key was NOT called since store is not loaded
        bot.client.request_room_key.assert_not_called()

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
        from nio import SyncResponse, Rooms
        # Create a properly initialized SyncResponse with all required arguments
        bot.client.sync.return_value = SyncResponse(
            next_batch="s123456",
            rooms=Rooms({}, {}, {}),
            device_key_count={},
            device_list={},
            to_device_events=[],
            presence_events=[]
        )
        
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

    def test_login_fails_with_empty_user_id(self):
        """Test that login fails gracefully when user_id is not set."""
        # Configure with empty user_id
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.com',
            'user_id': '',  # Empty user_id
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'token',
            'access_token': 'test_token_12345'
        }
        
        bot = ChatrixBot(self.config)
        
        # Mock the auth handler
        bot.auth.get_access_token = AsyncMock(return_value='test_token_12345')
        
        # Call login - should fail
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login failed
        self.assertFalse(result, "Login should fail with empty user_id")
        
        # Verify load_store was NOT called since we fail early
        # (we can't easily assert this without mocking, but the test will fail if it tries)

    def test_login_token_validates_user_id_before_load_store(self):
        """Test that user_id is validated before attempting to load store."""
        # Configure with missing user_id
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.com',
            'user_id': None,  # None user_id
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'token',
            'access_token': 'test_token_12345'
        }
        
        bot = ChatrixBot(self.config)
        
        # Mock client methods - these should NOT be called
        bot.client.load_store = AsyncMock()
        bot.auth.get_access_token = AsyncMock(return_value='test_token_12345')
        
        # Call login - should fail before calling load_store
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login failed
        self.assertFalse(result, "Login should fail with None user_id")
        
        # Verify load_store was NOT called
        bot.client.load_store.assert_not_called()

    def test_send_startup_message_greetings_disabled(self):
        """Test that startup message is skipped when greetings are disabled."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': False,
            'greeting_rooms': ['!test:example.com']
        }
        
        bot = ChatrixBot(self.config)
        bot.send_message = AsyncMock()
        
        self.loop.run_until_complete(bot.send_startup_message())
        
        # Should not send any messages
        bot.send_message.assert_not_called()

    def test_send_startup_message_no_greeting_rooms(self):
        """Test that startup message is skipped when no greeting rooms configured."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': True,
            'greeting_rooms': []
        }
        
        bot = ChatrixBot(self.config)
        bot.send_message = AsyncMock()
        
        self.loop.run_until_complete(bot.send_startup_message())
        
        # Should not send any messages
        bot.send_message.assert_not_called()

    def test_send_startup_message_success(self):
        """Test successful startup message sending."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': True,
            'greeting_rooms': ['!room1:example.com', '!room2:example.com'],
            'startup_message': 'Bot starting!'
        }
        
        bot = ChatrixBot(self.config)
        bot.send_message = AsyncMock()
        
        self.loop.run_until_complete(bot.send_startup_message())
        
        # Should send messages to both rooms
        self.assertEqual(bot.send_message.call_count, 2)
        
        # Verify the message content
        calls = bot.send_message.call_args_list
        self.assertEqual(calls[0][0][0], '!room1:example.com')
        self.assertEqual(calls[0][0][1], 'Bot starting!')
        self.assertEqual(calls[1][0][0], '!room2:example.com')
        self.assertEqual(calls[1][0][1], 'Bot starting!')

    def test_send_startup_message_with_failure(self):
        """Test startup message with one room failing."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': True,
            'greeting_rooms': ['!room1:example.com', '!room2:example.com'],
            'startup_message': 'Bot starting!'
        }
        
        bot = ChatrixBot(self.config)
        
        # Make first call fail, second succeed
        bot.send_message = AsyncMock(side_effect=[
            Exception("Network error"),
            None
        ])
        
        # Should not raise exception
        self.loop.run_until_complete(bot.send_startup_message())
        
        # Should have tried to send to both rooms
        self.assertEqual(bot.send_message.call_count, 2)

    def test_send_shutdown_message_greetings_disabled(self):
        """Test that shutdown message is skipped when greetings are disabled."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': False,
            'greeting_rooms': ['!test:example.com']
        }
        
        bot = ChatrixBot(self.config)
        bot.send_message = AsyncMock()
        
        self.loop.run_until_complete(bot.send_shutdown_message())
        
        # Should not send any messages
        bot.send_message.assert_not_called()

    def test_send_shutdown_message_success(self):
        """Test successful shutdown message sending."""
        self.config.get_bot_config.return_value = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': [],
            'greetings_enabled': True,
            'greeting_rooms': ['!room1:example.com', '!room2:example.com'],
            'shutdown_message': 'Bot stopping!'
        }
        
        bot = ChatrixBot(self.config)
        bot.send_message = AsyncMock()
        
        self.loop.run_until_complete(bot.send_shutdown_message())
        
        # Should send messages to both rooms
        self.assertEqual(bot.send_message.call_count, 2)
        
        # Verify the message content
        calls = bot.send_message.call_args_list
        self.assertEqual(calls[0][0][0], '!room1:example.com')
        self.assertEqual(calls[0][0][1], 'Bot stopping!')

    def test_invite_callback(self):
        """Test that bot accepts room invites."""
        bot = ChatrixBot(self.config)
        bot.client.join = AsyncMock()
        
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!newroom:example.com'
        room.display_name = 'New Room'
        
        event = MagicMock()
        event.sender = '@inviter:example.com'
        
        self.loop.run_until_complete(bot.invite_callback(room, event))
        
        # Should join the room
        bot.client.join.assert_called_once_with('!newroom:example.com')

    def test_send_message_plain_text(self):
        """Test sending plain text message."""
        bot = ChatrixBot(self.config)
        bot.client.room_send = AsyncMock()
        
        self.loop.run_until_complete(
            bot.send_message('!test:example.com', 'Hello world')
        )
        
        # Verify message was sent
        bot.client.room_send.assert_called_once()
        call_args = bot.client.room_send.call_args
        
        self.assertEqual(call_args[1]['room_id'], '!test:example.com')
        self.assertEqual(call_args[1]['message_type'], 'm.room.message')
        self.assertEqual(call_args[1]['content']['body'], 'Hello world')
        self.assertEqual(call_args[1]['content']['msgtype'], 'm.text')

    def test_send_message_with_formatting(self):
        """Test sending message with HTML formatting."""
        bot = ChatrixBot(self.config)
        bot.client.room_send = AsyncMock()
        
        self.loop.run_until_complete(
            bot.send_message(
                '!test:example.com',
                'Hello world',
                '<b>Hello world</b>'
            )
        )
        
        # Verify formatted message was sent
        bot.client.room_send.assert_called_once()
        call_args = bot.client.room_send.call_args
        
        content = call_args[1]['content']
        self.assertEqual(content['body'], 'Hello world')
        self.assertEqual(content['formatted_body'], '<b>Hello world</b>')
        self.assertEqual(content['format'], 'org.matrix.custom.html')


if __name__ == '__main__':
    unittest.main()
