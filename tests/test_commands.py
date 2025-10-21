"""Tests for command handler module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from nio import MatrixRoom, RoomMessageText
from chatrixcd.commands import CommandHandler


class TestCommandHandler(unittest.TestCase):
    """Test CommandHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Mock bot
        self.mock_bot = MagicMock()
        self.mock_bot.send_message = AsyncMock()
        
        # Mock semaphore client
        self.mock_semaphore = MagicMock()
        
        # Config
        self.config = {
            'command_prefix': '!cd',
            'allowed_rooms': [],
            'admin_users': []
        }
        
        self.handler = CommandHandler(
            bot=self.mock_bot,
            config=self.config,
            semaphore=self.mock_semaphore
        )

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    def test_init(self):
        """Test handler initialization."""
        self.assertEqual(self.handler.command_prefix, '!cd')
        self.assertEqual(self.handler.allowed_rooms, [])
        self.assertEqual(self.handler.admin_users, [])
        self.assertEqual(self.handler.active_tasks, {})

    def test_is_allowed_room_no_restrictions(self):
        """Test room permission check with no restrictions."""
        result = self.handler.is_allowed_room('!test:example.com')
        self.assertTrue(result)

    def test_is_allowed_room_with_restrictions_allowed(self):
        """Test room permission check when room is in allowed list."""
        self.handler.allowed_rooms = ['!allowed:example.com']
        result = self.handler.is_allowed_room('!allowed:example.com')
        self.assertTrue(result)

    def test_is_allowed_room_with_restrictions_denied(self):
        """Test room permission check when room is not in allowed list."""
        self.handler.allowed_rooms = ['!allowed:example.com']
        result = self.handler.is_allowed_room('!denied:example.com')
        self.assertFalse(result)

    def test_is_admin_no_restrictions(self):
        """Test admin check with no restrictions."""
        result = self.handler.is_admin('@user:example.com')
        self.assertTrue(result)

    def test_is_admin_with_restrictions_allowed(self):
        """Test admin check when user is in admin list."""
        self.handler.admin_users = ['@admin:example.com']
        result = self.handler.is_admin('@admin:example.com')
        self.assertTrue(result)

    def test_is_admin_with_restrictions_denied(self):
        """Test admin check when user is not in admin list."""
        self.handler.admin_users = ['@admin:example.com']
        result = self.handler.is_admin('@user:example.com')
        self.assertFalse(result)
    
    def test_is_admin_url_encoded_username(self):
        """Test admin check with URL-encoded username."""
        self.handler.admin_users = ['@user%40domain.com:example.com']
        # Test with encoded username
        result = self.handler.is_admin('@user%40domain.com:example.com')
        self.assertTrue(result)
        # Test with decoded username
        result = self.handler.is_admin('@user@domain.com:example.com')
        self.assertTrue(result)
    
    def test_is_admin_url_encoded_in_config_decoded_in_request(self):
        """Test admin check when config has encoded username but request is decoded."""
        self.handler.admin_users = ['@chrisw%40privacyinternational.org:privacyinternational.org']
        result = self.handler.is_admin('@chrisw@privacyinternational.org:privacyinternational.org')
        self.assertTrue(result)
    
    def test_is_admin_decoded_in_config_encoded_in_request(self):
        """Test admin check when config has decoded username but request is encoded."""
        self.handler.admin_users = ['@chrisw@privacyinternational.org:privacyinternational.org']
        result = self.handler.is_admin('@chrisw%40privacyinternational.org:privacyinternational.org')
        self.assertTrue(result)

    def test_handle_message_ignores_non_command(self):
        """Test that non-command messages are ignored."""
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!test:example.com'
        
        event = MagicMock(spec=RoomMessageText)
        event.body = 'Just a regular message'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        self.loop.run_until_complete(self.handler.handle_message(room, event))
        
        # Should not send any response
        self.mock_bot.send_message.assert_not_called()

    def test_handle_message_in_non_allowed_room(self):
        """Test that commands in non-allowed rooms are ignored."""
        self.handler.allowed_rooms = ['!allowed:example.com']
        
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!denied:example.com'
        
        event = MagicMock(spec=RoomMessageText)
        event.body = '!cd help'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        self.loop.run_until_complete(self.handler.handle_message(room, event))
        
        # Should not send any response
        self.mock_bot.send_message.assert_not_called()

    def test_handle_message_empty_command(self):
        """Test that empty command shows help."""
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!test:example.com'
        
        event = MagicMock(spec=RoomMessageText)
        event.body = '!cd'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        self.loop.run_until_complete(self.handler.handle_message(room, event))
        
        # Should send help message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('ChatrixCD Bot Commands', call_args[1])

    def test_handle_message_help_command(self):
        """Test help command."""
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!test:example.com'
        
        event = MagicMock(spec=RoomMessageText)
        event.body = '!cd help'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        self.loop.run_until_complete(self.handler.handle_message(room, event))
        
        # Should send help message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('ChatrixCD Bot Commands', call_args[1])

    def test_handle_message_unknown_command(self):
        """Test unknown command."""
        room = MagicMock(spec=MatrixRoom)
        room.room_id = '!test:example.com'
        
        event = MagicMock(spec=RoomMessageText)
        event.body = '!cd invalidcmd'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        self.loop.run_until_complete(self.handler.handle_message(room, event))
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Unknown command', call_args[1])

    def test_list_projects_success(self):
        """Test list projects command with successful response."""
        # Mock semaphore response
        self.mock_semaphore.get_projects = AsyncMock(return_value=[
            {'id': 1, 'name': 'Project 1'},
            {'id': 2, 'name': 'Project 2'}
        ])
        
        self.loop.run_until_complete(
            self.handler.list_projects('!test:example.com')
        )
        
        # Should send projects list
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Available Projects', call_args[1])
        self.assertIn('Project 1', call_args[1])
        self.assertIn('Project 2', call_args[1])

    def test_list_projects_empty(self):
        """Test list projects command with no projects."""
        self.mock_semaphore.get_projects = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.list_projects('!test:example.com')
        )
        
        # Should send empty message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No projects found', call_args[1])

    def test_list_templates_no_args(self):
        """Test list templates without project ID."""
        # Mock to return multiple projects so it doesn't auto-select
        self.mock_semaphore.get_projects = AsyncMock(return_value=[
            {'id': 1, 'name': 'Project 1'},
            {'id': 2, 'name': 'Project 2'}
        ])
        
        self.loop.run_until_complete(
            self.handler.list_templates('!test:example.com', [])
        )
        
        # Should send usage message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Usage', call_args[1])

    def test_list_templates_invalid_project_id(self):
        """Test list templates with invalid project ID."""
        self.loop.run_until_complete(
            self.handler.list_templates('!test:example.com', ['invalid'])
        )
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Invalid project ID', call_args[1])

    def test_list_templates_success(self):
        """Test list templates with successful response."""
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[
            {'id': 1, 'name': 'Template 1', 'description': 'Test'},
            {'id': 2, 'name': 'Template 2'}
        ])
        
        self.loop.run_until_complete(
            self.handler.list_templates('!test:example.com', ['1'])
        )
        
        # Should send templates list
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('templates for project', call_args[1].lower())
        self.assertIn('Template 1', call_args[1])

    def test_list_templates_empty(self):
        """Test list templates with no templates."""
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.list_templates('!test:example.com', ['1'])
        )
        
        # Should send empty message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No templates found', call_args[1])

    def test_run_task_no_args(self):
        """Test run task without arguments."""
        # Mock to return multiple projects so it doesn't auto-select
        self.mock_semaphore.get_projects = AsyncMock(return_value=[
            {'id': 1, 'name': 'Project 1'},
            {'id': 2, 'name': 'Project 2'}
        ])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', [])
        )
        
        # Should send usage message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Usage', call_args[1])

    def test_run_task_insufficient_args(self):
        """Test run task with insufficient arguments."""
        # Mock to return multiple templates so it doesn't auto-select
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[
            {'id': 1, 'name': 'Template 1'},
            {'id': 2, 'name': 'Template 2'}
        ])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', ['1'])
        )
        
        # Should send message about multiple templates
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Multiple templates', call_args[1])

    def test_run_task_invalid_ids(self):
        """Test run task with invalid IDs."""
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', ['invalid', 'ids'])
        )
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Invalid project or template ID', call_args[1])

    @patch('asyncio.create_task')
    def test_run_task_success(self, mock_create_task):
        """Test successful task start - now requests confirmation."""
        # Mock template data
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[
            {'id': 1, 'name': 'Template 1', 'description': 'Test template'}
        ])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', ['1', '1'])
        )
        
        # Should send confirmation request
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Confirm', call_args[1])
        
        # Check that confirmation was added
        confirmation_key = '!test:example.com:@user:example.com'
        self.assertIn(confirmation_key, self.handler.pending_confirmations)

    def test_run_task_failure(self):
        """Test task start failure."""
        # Mock template data  
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', ['1', '1'])
        )
        
        # Should send template not found message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('not found', call_args[1])

    def test_check_status_no_args(self):
        """Test check status without task ID."""
        self.loop.run_until_complete(
            self.handler.check_status('!test:example.com', [])
        )
        
        # Should send usage message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Usage', call_args[1])

    def test_check_status_invalid_task_id(self):
        """Test check status with invalid task ID."""
        self.loop.run_until_complete(
            self.handler.check_status('!test:example.com', ['invalid'])
        )
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Invalid task ID', call_args[1])

    def test_check_status_task_not_found(self):
        """Test check status for task not in active tasks."""
        self.loop.run_until_complete(
            self.handler.check_status('!test:example.com', ['999'])
        )
        
        # Should send not found message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('not found in active tasks', call_args[1])

    def test_check_status_success(self):
        """Test successful status check."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        self.mock_semaphore.get_task_status = AsyncMock(return_value={
            'id': 123,
            'status': 'running',
            'start': '2024-01-01T00:00:00Z'
        })
        
        self.loop.run_until_complete(
            self.handler.check_status('!test:example.com', ['123'])
        )
        
        # Should send status message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('running', call_args[1])

    def test_stop_task_no_args(self):
        """Test stop task without task ID."""
        self.loop.run_until_complete(
            self.handler.stop_task('!test:example.com', '@user:example.com', [])
        )
        
        # Should send usage message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Usage', call_args[1])

    def test_stop_task_invalid_task_id(self):
        """Test stop task with invalid task ID."""
        self.loop.run_until_complete(
            self.handler.stop_task('!test:example.com', '@user:example.com', ['invalid'])
        )
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Invalid task ID', call_args[1])

    def test_stop_task_not_found(self):
        """Test stop task not in active tasks."""
        self.loop.run_until_complete(
            self.handler.stop_task('!test:example.com', '@user:example.com', ['999'])
        )
        
        # Should send not found message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('not found in active tasks', call_args[1])

    def test_stop_task_success(self):
        """Test successful task stop."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        self.mock_semaphore.stop_task = AsyncMock(return_value=True)
        
        self.loop.run_until_complete(
            self.handler.stop_task('!test:example.com', '@user:example.com', ['123'])
        )
        
        # Should send success message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('stopped', call_args[1])
        
        # Task should be removed from active tasks
        self.assertNotIn(123, self.handler.active_tasks)

    def test_stop_task_failure(self):
        """Test task stop failure."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        self.mock_semaphore.stop_task = AsyncMock(return_value=False)
        
        self.loop.run_until_complete(
            self.handler.stop_task('!test:example.com', '@user:example.com', ['123'])
        )
        
        # Should send failure message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Failed to stop', call_args[1])

    def test_get_logs_no_args(self):
        """Test get logs without task ID."""
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', [])
        )
        
        # Should send usage message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Usage', call_args[1])

    def test_get_logs_invalid_task_id(self):
        """Test get logs with invalid task ID."""
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', ['invalid'])
        )
        
        # Should send error message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Invalid task ID', call_args[1])

    def test_get_logs_task_not_found(self):
        """Test get logs for task not in active tasks."""
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', ['999'])
        )
        
        # Should send not found message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('not found in active tasks', call_args[1])

    def test_get_logs_success(self):
        """Test successful logs retrieval."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        self.mock_semaphore.get_task_output = AsyncMock(return_value='Task output logs')
        
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', ['123'])
        )
        
        # Should send logs message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Logs for Task', call_args[1])
        self.assertIn('Task output logs', call_args[1])

    def test_get_logs_empty(self):
        """Test logs retrieval with no logs."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        self.mock_semaphore.get_task_output = AsyncMock(return_value=None)
        
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', ['123'])
        )
        
        # Should send no logs message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No logs available', call_args[1])

    def test_get_logs_truncation(self):
        """Test logs truncation for very long output."""
        # Add task to active tasks
        self.handler.active_tasks[123] = {
            'project_id': 1,
            'room_id': '!test:example.com'
        }
        
        # Create very long logs with many lines
        long_logs = '\n'.join(['A' * 100 for _ in range(200)])
        self.mock_semaphore.get_task_output = AsyncMock(return_value=long_logs)
        
        self.loop.run_until_complete(
            self.handler.get_logs('!test:example.com', ['123'])
        )
        
        # Should send truncated logs (last 100 lines)
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('last 100 lines', call_args[1])


    def test_get_display_name(self):
        """Test getting display name from user ID."""
        # Test with standard Matrix user ID
        result = self.handler._get_display_name('@john:example.com')
        self.assertEqual(result, 'john')
        
        # Test with user ID containing @ symbol
        result = self.handler._get_display_name('@user@domain.com:server.com')
        self.assertEqual(result, 'user@domain.com')
        
        # Test with invalid user ID
        result = self.handler._get_display_name('invalid')
        self.assertEqual(result, 'invalid')
    
    def test_get_greeting(self):
        """Test getting random greeting for a user."""
        # Test that greeting is generated
        greeting = self.handler._get_greeting('@john:example.com')
        self.assertIsInstance(greeting, str)
        
        # Test that greeting contains the user's name or just emoji
        # (since we have one greeting that's just "👋")
        self.assertTrue(len(greeting) > 0)
        
        # Test that multiple calls may return different greetings
        # (though with randomness, we can't guarantee they'll be different)
        greetings = set()
        for _ in range(50):
            greeting = self.handler._get_greeting('@test:example.com')
            greetings.add(greeting)
        
        # With 16 different greetings, we should get multiple unique ones
        self.assertGreater(len(greetings), 1)
        
        # Test with non-standard user ID
        greeting = self.handler._get_greeting('someuser')
        self.assertIsInstance(greeting, str)

    def test_format_description_with_paragraph_symbol(self):
        """Test formatting descriptions with ¶ symbol."""
        # Test with ¶ symbol
        description = "First paragraph¶Second paragraph¶Third paragraph"
        result = self.handler._format_description(description)
        self.assertEqual(result, "First paragraph\n\nSecond paragraph\n\nThird paragraph")
        
        # Test without ¶ symbol
        description = "Simple description"
        result = self.handler._format_description(description)
        self.assertEqual(result, "Simple description")
        
        # Test with empty description
        result = self.handler._format_description("")
        self.assertEqual(result, "")
        
        # Test with None
        result = self.handler._format_description(None)
        self.assertIsNone(result)

    def test_handle_pet_command(self):
        """Test the secret pet command."""
        self.loop.run_until_complete(
            self.handler.handle_pet('!test:example.com', '@user:example.com', 'event123')
        )
        
        # Should send a positive response
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        message = call_args[0][1]
        reply_to = call_args[1].get('reply_to_event_id')
        
        # Should include user name and be positive
        self.assertIn('user', message)
        self.assertTrue(any(emoji in message for emoji in ['🥰', '😊', '💙', '🤗', '😄', '🌟', '🐕', '💻', '😳', '☺️']))
        
        # Should reply to the original message
        self.assertEqual(reply_to, 'event123')

    def test_handle_scold_command(self):
        """Test the secret scold command."""
        self.loop.run_until_complete(
            self.handler.handle_scold('!test:example.com', '@user:example.com', 'event123')
        )
        
        # Should send an apologetic response
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        message = call_args[0][1]
        reply_to = call_args[1].get('reply_to_event_id')
        
        # Should include user name and be apologetic
        self.assertIn('user', message)
        self.assertTrue(any(emoji in message for emoji in ['😢', '😔', '💔', '😞', '😭', '😐', '😟', '😓', '🥺', '😅']))
        
        # Should reply to the original message
        self.assertEqual(reply_to, 'event123')

    def test_handle_message_with_threading(self):
        """Test that messages include threading support."""
        # Create a mock event
        event = MagicMock()
        event.body = '!cd help'
        event.sender = '@user:example.com'
        event.event_id = 'event123'
        
        # Create a mock room
        room = MagicMock()
        room.room_id = '!test:example.com'
        
        self.loop.run_until_complete(
            self.handler.handle_message(room, event)
        )
        
        # Should send help message with reply_to_event_id
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        reply_to = call_args[1].get('reply_to_event_id')
        
        # Should reply to the original message
        self.assertEqual(reply_to, 'event123')

    def test_handle_reaction_positive(self):
        """Test handling positive reaction to confirmation."""
        # Set up a pending confirmation
        confirmation_key = '!test:example.com:@user:example.com'
        self.handler.pending_confirmations[confirmation_key] = {
            'project_id': 1,
            'template_id': 2,
            'template_name': 'Test Template',
            'sender': '@user:example.com',
            'room_id': '!test:example.com',
            'timestamp': 123456
        }
        self.handler.confirmation_message_ids[confirmation_key] = 'msg123'
        
        # Mock the semaphore start_task
        self.mock_semaphore.start_task = AsyncMock(return_value={'id': 999})
        
        # Create mock room
        room = MagicMock()
        room.room_id = '!test:example.com'
        
        # Test thumbs up reaction
        self.loop.run_until_complete(
            self.handler.handle_reaction(room, '@user:example.com', 'msg123', '👍')
        )
        
        # Confirmation should be removed
        self.assertNotIn(confirmation_key, self.handler.pending_confirmations)
        self.assertNotIn(confirmation_key, self.handler.confirmation_message_ids)
        
        # Task should be started
        self.mock_semaphore.start_task.assert_called_once_with(1, 2)

    def test_handle_reaction_negative(self):
        """Test handling negative reaction to confirmation."""
        # Set up a pending confirmation
        confirmation_key = '!test:example.com:@user:example.com'
        self.handler.pending_confirmations[confirmation_key] = {
            'project_id': 1,
            'template_id': 2,
            'template_name': 'Test Template',
            'sender': '@user:example.com',
            'room_id': '!test:example.com',
            'timestamp': 123456
        }
        self.handler.confirmation_message_ids[confirmation_key] = 'msg123'
        
        # Create mock room
        room = MagicMock()
        room.room_id = '!test:example.com'
        
        # Test thumbs down reaction
        self.loop.run_until_complete(
            self.handler.handle_reaction(room, '@user:example.com', 'msg123', '👎')
        )
        
        # Confirmation should be removed
        self.assertNotIn(confirmation_key, self.handler.pending_confirmations)
        self.assertNotIn(confirmation_key, self.handler.confirmation_message_ids)
        
        # Should send cancellation message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        # Check for any cancellation-related words
        message_lower = call_args[1].lower()
        self.assertTrue(
            any(word in message_lower for word in ['cancel', 'stop', 'alright', '❌', '🛑', '✋']),
            f"Expected cancellation message but got: {call_args[1]}"
        )

    def test_handle_reaction_wrong_user(self):
        """Test that reactions from wrong user are rejected."""
        # Set up a pending confirmation
        confirmation_key = '!test:example.com:@user:example.com'
        self.handler.pending_confirmations[confirmation_key] = {
            'project_id': 1,
            'template_id': 2,
            'template_name': 'Test Template',
            'sender': '@user:example.com',
            'room_id': '!test:example.com',
            'timestamp': 123456
        }
        self.handler.confirmation_message_ids[confirmation_key] = 'msg123'
        
        # Create mock room
        room = MagicMock()
        room.room_id = '!test:example.com'
        
        # Test reaction from different user
        self.loop.run_until_complete(
            self.handler.handle_reaction(room, '@other:example.com', 'msg123', '👍')
        )
        
        # Confirmation should still exist
        self.assertIn(confirmation_key, self.handler.pending_confirmations)
        
        # Should send rejection message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Only', call_args[1])


if __name__ == '__main__':
    unittest.main()
