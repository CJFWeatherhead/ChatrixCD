"""Tests for bot module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
import os
import time
import tempfile
from nio import MegolmEvent, MatrixRoom, RoomMessageText, SyncResponse, Rooms
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
            'homeserver': 'https://matrix.example.test',
            'user_id': '@bot:example.test',
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'password',
            'password': 'testpass'
        }
        self.config.get_semaphore_config.return_value = {
            'url': 'https://semaphore.example.test',
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
        self.assertEqual(bot.user_id, '@bot:example.test')
        self.assertEqual(bot.client.user_id, '@bot:example.test')
        self.assertEqual(bot.client.user, '@bot:example.test')
        
        # Ensure user_id is not empty (important for load_store())
        self.assertTrue(bot.client.user_id)

    def test_init_sets_start_time(self):
        """Test that bot initialization sets start_time to track when bot started."""
        import time
        
        # Record time before creating bot
        before_time = int(time.time() * 1000)
        
        bot = ChatrixBot(self.config)
        
        # Record time after creating bot
        after_time = int(time.time() * 1000)
        
        # Verify start_time is set and within reasonable range
        self.assertIsNotNone(bot.start_time)
        self.assertGreaterEqual(bot.start_time, before_time)
        self.assertLessEqual(bot.start_time, after_time)
    
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
        event.decrypted = None  # Message couldn't be decrypted
        
        # Call the callback
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
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
        event.decrypted = None  # Message couldn't be decrypted
        
        # Call the callback - should not raise an exception
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
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
        event.server_timestamp = bot.start_time + 1000  # Message sent after bot started
        
        # Call the callback
        self.loop.run_until_complete(
            bot.message_callback(room, event)
        )
        
        # Verify handle_message WAS called
        bot.command_handler.handle_message.assert_called_once_with(room, event)

    def test_message_callback_ignores_old_messages(self):
        """Test that message callback ignores messages sent before bot started."""
        bot = ChatrixBot(self.config)
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room and event from another user
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        
        event = MagicMock(spec=RoomMessageText)
        event.sender = "@other:example.com"  # Different user
        event.body = "!cd help"
        event.server_timestamp = bot.start_time - 10000  # Message sent before bot started
        
        # Call the callback
        self.loop.run_until_complete(
            bot.message_callback(room, event)
        )
        
        # Verify handle_message was NOT called
        bot.command_handler.handle_message.assert_not_called()

    def test_message_callback_processes_messages_at_start_time(self):
        """Test that message callback processes messages sent exactly at bot start time."""
        bot = ChatrixBot(self.config)
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room and event from another user
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        
        event = MagicMock(spec=RoomMessageText)
        event.sender = "@other:example.com"  # Different user
        event.body = "!cd help"
        event.server_timestamp = bot.start_time  # Message sent exactly at bot start time
        
        # Call the callback
        self.loop.run_until_complete(
            bot.message_callback(room, event)
        )
        
        # Verify handle_message WAS called (>= comparison, not >)
        bot.command_handler.handle_message.assert_called_once_with(room, event)

    def test_login_oidc_uses_default_redirect_url(self):
        """Test that OIDC authentication uses default redirect URL when not specified."""
        # Configure for OIDC authentication without explicit redirect URL
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.test',
            'user_id': '@bot:example.test',
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'oidc'
            # Missing oidc_redirect_url - should use default
        }
        
        bot = ChatrixBot(self.config)
        
        # Verify that the auth handler returns the default redirect URL
        redirect_url = bot.auth.get_oidc_redirect_url()
        self.assertEqual(redirect_url, 'http://localhost:8080/callback', 
                        "Should use default redirect URL when not configured")
        
        # Verify validation passes
        is_valid, error_msg = bot.auth.validate_config()
        self.assertTrue(is_valid, "OIDC validation should pass with default redirect URL")
        self.assertIsNone(error_msg)

    def test_login_fails_with_empty_user_id(self):
        """Test that login fails gracefully when user_id is not set."""
        # Configure with empty user_id
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.test',
            'user_id': '',  # Empty user_id
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'password',
            'password': 'testpass'
        }
        
        bot = ChatrixBot(self.config)
        
        # Mock client login to ensure it's not called
        bot.client.login = AsyncMock()
        
        # Call login - should fail early due to empty user_id
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login failed
        self.assertFalse(result, "Login should fail with empty user_id")
        
        # Verify client.login was NOT called (failed validation before that)
        bot.client.login.assert_not_called()

    def test_login_password_validates_user_id(self):
        """Test that user_id is validated before attempting to login."""
        # Configure with missing user_id
        self.config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.test',
            'user_id': None,  # None user_id
            'device_id': 'TESTDEVICE',
            'device_name': 'Test Bot',
            'store_path': self.temp_dir,
            'auth_type': 'password',
            'password': 'testpass'
        }
        
        bot = ChatrixBot(self.config)
        
        # Mock client methods - these should NOT be called
        bot.client.login = AsyncMock()
        
        # Call login - should fail before calling client.login
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login failed
        self.assertFalse(result, "Login should fail with None user_id")
        
        # Verify client.login was NOT called
        bot.client.login.assert_not_called()

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

    def test_setup_encryption_uploads_keys(self):
        """Test that encryption setup uploads keys when needed."""
        bot = ChatrixBot(self.config)
        
        # Mock encryption support
        bot.client.olm = MagicMock()
        # Use PropertyMock for read-only properties
        type(bot.client).should_upload_keys = unittest.mock.PropertyMock(return_value=True)
        type(bot.client).should_query_keys = unittest.mock.PropertyMock(return_value=False)
        bot.client.keys_upload = AsyncMock()
        
        # Setup encryption
        result = self.loop.run_until_complete(bot.setup_encryption())
        
        # Verify success and keys_upload was called
        self.assertTrue(result)
        bot.client.keys_upload.assert_called_once()

    def test_setup_encryption_queries_device_keys(self):
        """Test that encryption setup queries device keys when needed."""
        bot = ChatrixBot(self.config)
        
        # Mock encryption support
        bot.client.olm = MagicMock()
        # Use PropertyMock for read-only properties
        type(bot.client).should_upload_keys = unittest.mock.PropertyMock(return_value=False)
        type(bot.client).should_query_keys = unittest.mock.PropertyMock(return_value=True)
        bot.client.keys_query = AsyncMock()
        
        # Setup encryption
        result = self.loop.run_until_complete(bot.setup_encryption())
        
        # Verify success and keys_query was called
        self.assertTrue(result)
        bot.client.keys_query.assert_called_once()

    def test_setup_encryption_skips_when_not_enabled(self):
        """Test that encryption setup is skipped when encryption is not enabled."""
        bot = ChatrixBot(self.config)
        
        # Mock no encryption support
        bot.client.olm = None
        bot.client.keys_upload = AsyncMock()
        
        # Setup encryption
        result = self.loop.run_until_complete(bot.setup_encryption())
        
        # Verify it returns True but doesn't upload keys
        self.assertTrue(result)
        bot.client.keys_upload.assert_not_called()

    def test_decryption_failure_prevents_duplicate_requests(self):
        """Test that decryption failure callback prevents duplicate key requests."""
        bot = ChatrixBot(self.config)
        
        # Mock the request_room_key method and store/olm
        bot.client.request_room_key = AsyncMock()
        bot.client.store = MagicMock()
        bot.client.olm = MagicMock()
        
        # Create mock room and event
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        event = MagicMock(spec=MegolmEvent)
        event.sender = "@user:example.com"
        event.session_id = "test_session_id_123"
        event.decrypted = None  # Message couldn't be decrypted
        
        # Call the callback twice with the same session_id
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
        )
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
        )
        
        # Verify request_room_key was only called once
        bot.client.request_room_key.assert_called_once_with(event)
        
        # Verify the session_id was tracked
        self.assertIn("test_session_id_123", bot.requested_session_ids)

    def test_decryption_failure_allows_different_sessions(self):
        """Test that different session IDs are each requested once."""
        bot = ChatrixBot(self.config)
        
        # Mock the request_room_key method and store/olm
        bot.client.request_room_key = AsyncMock()
        bot.client.store = MagicMock()
        bot.client.olm = MagicMock()
        
        # Create mock room
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        # Create two events with different session IDs
        event1 = MagicMock(spec=MegolmEvent)
        event1.sender = "@user:example.com"
        event1.session_id = "session_1"
        event1.decrypted = None  # Message couldn't be decrypted
        
        event2 = MagicMock(spec=MegolmEvent)
        event2.sender = "@user:example.com"
        event2.session_id = "session_2"
        event2.decrypted = None  # Message couldn't be decrypted
        
        # Call the callback with both events
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event1)
        )
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event2)
        )
        
        # Verify request_room_key was called twice (once for each session)
        self.assertEqual(bot.client.request_room_key.call_count, 2)
        
        # Verify both session IDs were tracked
        self.assertIn("session_1", bot.requested_session_ids)
        self.assertIn("session_2", bot.requested_session_ids)

    def test_megolm_event_processes_decrypted_messages(self):
        """Test that successfully decrypted Megolm events are processed as messages."""
        bot = ChatrixBot(self.config)
        
        # Mock the command handler
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        # Create a decrypted text message
        decrypted_event = MagicMock(spec=RoomMessageText)
        decrypted_event.sender = "@user:example.com"
        decrypted_event.body = "!cd help"
        decrypted_event.server_timestamp = int(time.time() * 1000)
        
        # Create a MegolmEvent with the decrypted content
        event = MagicMock(spec=MegolmEvent)
        event.sender = "@user:example.com"
        event.session_id = "test_session_id"
        event.decrypted = decrypted_event  # Message was successfully decrypted
        
        # Call the callback
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
        )
        
        # Verify the message was processed
        bot.command_handler.handle_message.assert_called_once()
        # Check that the decrypted event was passed to the handler
        call_args = bot.command_handler.handle_message.call_args[0]
        self.assertEqual(call_args[0], room)
        self.assertEqual(call_args[1], decrypted_event)

    def test_megolm_event_ignores_decrypted_non_text(self):
        """Test that decrypted non-text Megolm events are ignored."""
        bot = ChatrixBot(self.config)
        
        # Mock the command handler
        bot.command_handler.handle_message = AsyncMock()
        
        # Create mock room
        room = MagicMock(spec=MatrixRoom)
        room.display_name = "Test Room"
        room.room_id = "!test:example.com"
        
        # Create a decrypted non-text event (e.g., image)
        from nio import RoomMessageImage
        decrypted_event = MagicMock(spec=RoomMessageImage)
        decrypted_event.sender = "@user:example.com"
        
        # Create a MegolmEvent with the decrypted content
        event = MagicMock(spec=MegolmEvent)
        event.sender = "@user:example.com"
        event.session_id = "test_session_id"
        event.decrypted = decrypted_event  # Message was successfully decrypted
        
        # Call the callback
        self.loop.run_until_complete(
            bot.megolm_event_callback(room, event)
        )
        
        # Verify the message was NOT processed (only text messages are handled)
        bot.command_handler.handle_message.assert_not_called()

    def test_sync_callback_uploads_keys(self):
        """Test that sync callback uploads keys when needed."""
        bot = ChatrixBot(self.config)
        
        # Mock encryption support
        bot.client.olm = MagicMock()
        # Use PropertyMock for read-only properties
        type(bot.client).should_upload_keys = unittest.mock.PropertyMock(return_value=True)
        type(bot.client).should_query_keys = unittest.mock.PropertyMock(return_value=False)
        bot.client.keys_upload = AsyncMock()
        
        # Create mock sync response
        response = SyncResponse(
            next_batch="s123456",
            rooms=Rooms({}, {}, {}),
            device_key_count={},
            device_list={},
            to_device_events=[],
            presence_events=[]
        )
        
        # Call sync callback
        self.loop.run_until_complete(bot.sync_callback(response))
        
        # Verify keys_upload was called
        bot.client.keys_upload.assert_called_once()

    def test_sync_callback_queries_keys(self):
        """Test that sync callback queries device keys when needed."""
        bot = ChatrixBot(self.config)
        
        # Mock encryption support
        bot.client.olm = MagicMock()
        # Use PropertyMock for read-only properties
        type(bot.client).should_upload_keys = unittest.mock.PropertyMock(return_value=False)
        type(bot.client).should_query_keys = unittest.mock.PropertyMock(return_value=True)
        bot.client.keys_query = AsyncMock()
        
        # Create mock sync response
        response = SyncResponse(
            next_batch="s123456",
            rooms=Rooms({}, {}, {}),
            device_key_count={},
            device_list={},
            to_device_events=[],
            presence_events=[]
        )
        
        # Call sync callback
        self.loop.run_until_complete(bot.sync_callback(response))
        
        # Verify keys_query was called
        bot.client.keys_query.assert_called_once()

    def test_login_password_with_nio_response(self):
        """Test password login using actual nio LoginResponse object."""
        from nio import LoginResponse
        
        bot = ChatrixBot(self.config)
        
        # Mock the login method to return a real LoginResponse
        login_response = LoginResponse(
            user_id='@bot:example.com',
            device_id='TESTDEVICE',
            access_token='test_access_token_xyz'
        )
        bot.client.login = AsyncMock(return_value=login_response)
        bot.client.sync = AsyncMock()
        
        # Call login
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login succeeded
        self.assertTrue(result)
        bot.client.login.assert_called_once()

    def test_login_handles_nio_error_response(self):
        """Test that login handles nio ErrorResponse properly."""
        from nio import LoginError
        
        bot = ChatrixBot(self.config)
        
        # Mock the login method to return an error
        error_response = LoginError(
            message='Invalid credentials',
            status_code='M_FORBIDDEN'
        )
        bot.client.login = AsyncMock(return_value=error_response)
        
        # Call login - should handle error gracefully
        result = self.loop.run_until_complete(bot.login())
        
        # Verify login failed
        self.assertFalse(result)

    def test_send_message_with_nio_error(self):
        """Test send_message handles nio error responses."""
        from nio import RoomSendError
        
        bot = ChatrixBot(self.config)
        
        # Mock room_send to return an error response
        error_response = RoomSendError(
            message='Room not found',
            status_code='M_NOT_FOUND'
        )
        bot.client.room_send = AsyncMock(return_value=error_response)
        
        # Call send_message - should not raise exception
        self.loop.run_until_complete(
            bot.send_message('!nonexistent:example.com', 'Test message')
        )
        
        # Verify the send was attempted
        bot.client.room_send.assert_called_once()

    def test_invite_callback_with_nio_join_response(self):
        """Test invite callback using nio JoinResponse."""
        from nio import JoinResponse, InviteMemberEvent
        
        bot = ChatrixBot(self.config)
        
        # Mock join to return a real JoinResponse
        join_response = JoinResponse(room_id='!newroom:example.com')
        bot.client.join = AsyncMock(return_value=join_response)
        
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!newroom:example.com'
        room.display_name = 'New Room'
        
        event = MagicMock(spec=InviteMemberEvent)
        event.sender = '@inviter:example.com'
        
        # Call the callback
        self.loop.run_until_complete(bot.invite_callback(room, event))
        
        # Verify join was called
        bot.client.join.assert_called_once_with('!newroom:example.com')

    def test_setup_encryption_with_nio_keys_upload_response(self):
        """Test encryption setup with nio KeysUploadResponse."""
        from nio import KeysUploadResponse
        
        bot = ChatrixBot(self.config)
        
        # Mock encryption support
        bot.client.olm = MagicMock()
        type(bot.client).should_upload_keys = unittest.mock.PropertyMock(return_value=True)
        type(bot.client).should_query_keys = unittest.mock.PropertyMock(return_value=False)
        
        # Mock keys_upload to return a real response with proper signature
        # KeysUploadResponse(curve25519_count, signed_curve25519_count)
        keys_response = KeysUploadResponse(curve25519_count=10, signed_curve25519_count=50)
        bot.client.keys_upload = AsyncMock(return_value=keys_response)
        
        # Setup encryption
        result = self.loop.run_until_complete(bot.setup_encryption())
        
        # Verify success
        self.assertTrue(result)
        bot.client.keys_upload.assert_called_once()

    def test_message_callback_with_nio_room_send_response(self):
        """Test message processing results in nio RoomSendResponse."""
        from nio import RoomSendResponse
        
        bot = ChatrixBot(self.config)
        
        # Mock command handler to send a response
        async def mock_handle_message(room, event):
            # Simulate sending a reply
            await bot.send_message(room.room_id, 'Response message')
        
        bot.command_handler.handle_message = AsyncMock(side_effect=mock_handle_message)
        
        # Mock room_send to return a real response with proper signature
        # RoomSendResponse(event_id, room_id)
        send_response = RoomSendResponse(
            event_id='$event123:example.com',
            room_id='!test:example.com'
        )
        bot.client.room_send = AsyncMock(return_value=send_response)
        
        # Create message event
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!test:example.com'
        room.display_name = 'Test Room'
        
        event = MagicMock(spec=RoomMessageText)
        event.sender = '@user:example.com'
        event.body = '!cd help'
        event.server_timestamp = bot.start_time + 1000
        
        # Process the message
        self.loop.run_until_complete(bot.message_callback(room, event))
        
        # Verify command was handled and response was sent
        bot.command_handler.handle_message.assert_called_once()
        bot.client.room_send.assert_called_once()


if __name__ == '__main__':
    unittest.main()
