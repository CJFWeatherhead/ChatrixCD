"""Tests for command handler module."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from nio import MatrixRoom, RoomMessageText
from chatrixcd.commands import CommandHandler
from chatrixcd.verification import SAS_AVAILABLE


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
        
        # Should send clear message about no projects (not connection error)
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No projects found', call_args[1])
        self.assertIn('Create a project', call_args[1])

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

    def test_run_task_no_templates_single_arg(self):
        """Test run task with zero templates when only project ID provided."""
        # Mock to return empty templates list
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', ['1'])
        )
        
        # Should send message about no templates
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No templates found', call_args[1])
        self.assertIn('Create a template', call_args[1])

    def test_run_task_no_templates_no_args(self):
        """Test run task with zero templates when no args provided and one project."""
        # Mock to return one project with no templates
        self.mock_semaphore.get_projects = AsyncMock(return_value=[
            {'id': 1, 'name': 'Project 1'}
        ])
        self.mock_semaphore.get_project_templates = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.run_task('!test:example.com', '@user:example.com', [])
        )
        
        # Should send message about no templates
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('No templates found', call_args[1])
        self.assertIn('Create a template', call_args[1])

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
        # Error message changed in refactored code
        self.assertIn('Could not retrieve task info', call_args[1])

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
        # Note: Format changed with refactoring - no longer includes "Task output logs"

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
        
        # Should send logs message (truncation happens in HTML formatting)
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        self.assertIn('Logs for Task', call_args[1])


    def test_get_display_name(self):
        """Test getting display name from user ID."""
        # Test with standard Matrix user ID - now returns full ID for proper mentions
        result = self.handler._get_display_name('@john:example.com')
        self.assertEqual(result, '@john:example.com')
        
        # Test with user ID containing @ symbol in username
        result = self.handler._get_display_name('@user@domain.com:server.com')
        self.assertEqual(result, '@user@domain.com:server.com')
        
        # Test with invalid user ID (no @ prefix) - returns as-is
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

        # Test that None user ID returns a greeting
        greeting = self.handler._get_greeting(None)
        self.assertIsInstance(greeting, str)
        self.assertGreater(len(greeting), 0)

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
            self.handler.handle_pet('!test:example.com', '@user:example.com')
        )
        
        # Should send a positive response
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        message = call_args[0][1]
        
        # Should include user name and be positive
        self.assertIn('user', message)
        self.assertTrue(any(emoji in message for emoji in ['🥰', '😊', '💙', '🤗', '😄', '🌟', '🐕', '💻', '😳', '☺️', '💕', '💖']))

    def test_handle_scold_command(self):
        """Test the secret scold command."""
        self.loop.run_until_complete(
            self.handler.handle_scold('!test:example.com', '@user:example.com')
        )
        
        # Should send an apologetic response
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args
        message = call_args[0][1]
        
        # Should include user name and be apologetic
        self.assertIn('user', message)
        self.assertTrue(any(emoji in message for emoji in ['😢', '😔', '💔', '😞', '😭', '😐', '😟', '😓', '🥺', '😅']))

    def test_handle_message_basic(self):
        """Test basic message handling."""
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
        
        # Should send help message
        self.mock_bot.send_message.assert_called_once()

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
        # Check for any cancellation-related words or new variations
        message_lower = call_args[1].lower()
        self.assertTrue(
            any(word in message_lower for word in ['cancel', 'stop', 'alright', 'nevermind', 'changed', '❌', '🛑', '✋', '🙅', '🤷']),
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


    def test_ansi_to_html_for_pre(self):
        """Test ANSI to HTML conversion for Matrix-compatible output."""
        # Test that ANSI codes are converted to Matrix-compatible HTML with data-mx-color
        text_with_color = "\x1b[31mRed text\x1b[0m"
        result = self.handler._ansi_to_html_for_pre(text_with_color)
        # Should contain HTML span tag with data-mx-color attribute (Matrix v1.10+ recommended)
        self.assertIn('<span data-mx-color="#cc0000">Red text</span>', result)
        self.assertNotIn('\x1b', result)  # No ANSI codes remaining
        self.assertNotIn('style=', result)  # No inline CSS styles
        
        # Test bold ANSI codes are converted to <strong> tags
        text_with_bold = "\x1b[1mBold text\x1b[0m"
        result = self.handler._ansi_to_html_for_pre(text_with_bold)
        # Should contain <strong> tag (Matrix-supported)
        self.assertIn('<strong>Bold text</strong>', result)
        self.assertNotIn('\x1b', result)
        
        # Test that newlines are preserved (not replaced with <br>)
        text_with_newlines = "Line 1\nLine 2\nLine 3"
        result = self.handler._ansi_to_html_for_pre(text_with_newlines)
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")
        self.assertNotIn('<br>', result)
        
        # Test mixed ANSI codes and text
        text_mixed = "Normal \x1b[32mgreen\x1b[0m text"
        result = self.handler._ansi_to_html_for_pre(text_mixed)
        # Should contain HTML span tag for green text
        self.assertIn('<span data-mx-color="#4e9a06">green</span>', result)
        self.assertIn('Normal', result)
        self.assertIn('text', result)

    def test_markdown_to_html_with_mentions(self):
        """Test markdown to HTML conversion with Matrix mentions."""
        # Test Matrix user mention conversion
        text = "Hello @user:example.com how are you?"
        result = self.handler.markdown_to_html(text)
        self.assertIn('<a href="https://matrix.to/#/@user:example.com">@user:example.com</a>', result)
        
        # Test bold with mentions
        text = "Hello @user:example.com **bold text** here"
        result = self.handler.markdown_to_html(text)
        self.assertIn('<a href="https://matrix.to/#/@user:example.com">@user:example.com</a>', result)
        self.assertIn('<strong>bold text</strong>', result)
        
        # Test multiple mentions
        text = "@user1:example.com and @user2:example.org"
        result = self.handler.markdown_to_html(text)
        self.assertIn('<a href="https://matrix.to/#/@user1:example.com">@user1:example.com</a>', result)
        self.assertIn('<a href="https://matrix.to/#/@user2:example.org">@user2:example.org</a>', result)
        
        # Test mention with special characters (underscore, plus, equals)
        text = "@user_name+test=foo:matrix.example.org"
        result = self.handler.markdown_to_html(text)
        self.assertIn('<a href="https://matrix.to/#/@user_name+test=foo:matrix.example.org">@user_name+test=foo:matrix.example.org</a>', result)

    def test_get_display_name_returns_full_id(self):
        """Test that _get_display_name returns full Matrix ID for proper mentions."""
        # Test with full Matrix ID
        user_id = "@user:example.com"
        result = self.handler._get_display_name(user_id)
        self.assertEqual(result, "@user:example.com")
        
        # Test with another format
        user_id = "@john.doe:matrix.org"
        result = self.handler._get_display_name(user_id)
        self.assertEqual(result, "@john.doe:matrix.org")

    def test_get_semaphore_info_includes_bot_version(self):
        """Test that get_semaphore_info includes bot version and system info."""
        # Mock semaphore info
        self.mock_semaphore.get_info = AsyncMock(return_value={
            'version': '2.8.0'
        })
        
        # Mock bot.get_status_info() to return proper status dictionary
        self.mock_bot.get_status_info = MagicMock(return_value={
            'version': '2025.11.15.5.2.0-c123456',
            'platform': 'Linux 5.15.0',
            'architecture': 'x86_64',
            'runtime': 'Python 3.12.0 (interpreter)',
            'cpu_percent': 2.5,
            'memory': {'percent': 15.3, 'used': 245, 'total': 1600},
            'metrics': {
                'messages_sent': 42,
                'requests_received': 15,
                'errors': 0,
                'emojis_used': 128
            },
            'matrix_status': 'Connected',
            'matrix_homeserver': 'https://matrix.example.com',
            'matrix_user_id': '@bot:example.com',
            'matrix_device_id': 'DEVICE123',
            'matrix_encrypted': True,
            'semaphore_status': 'Connected',
            'uptime': 7890000
        })
        
        # Mock bot client (still needed for some direct access)
        self.mock_bot.client = MagicMock()
        self.mock_bot.client.homeserver = 'https://matrix.example.com'
        self.mock_bot.client.user_id = '@bot:example.com'
        self.mock_bot.client.device_id = 'DEVICE123'
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.olm = MagicMock()  # E2E enabled
        
        self.loop.run_until_complete(
            self.handler.get_semaphore_info('!test:example.com', '@user:example.com')
        )
        
        # Should send info message
        self.mock_bot.send_message.assert_called_once()
        call_args = self.mock_bot.send_message.call_args[0]
        message = call_args[1]
        
        # Check for bot information
        self.assertIn('ChatrixCD Bot', message)
        self.assertIn('Version:', message)
        self.assertIn('Platform:', message)
        self.assertIn('Architecture:', message)
        self.assertIn('CPU Usage:', message)
        self.assertIn('Memory Usage:', message)
        
        # Check for Matrix information
        self.assertIn('Matrix Server', message)
        self.assertIn('@bot:example.com', message)
        
        # Check for Semaphore information
        self.assertIn('Semaphore Server', message)
        self.assertIn('2.8.0', message)

    def test_get_semaphore_info_respects_redact_flag(self):
        """Test that get_semaphore_info respects redact flag for IP addresses."""
        # Mock semaphore info
        self.mock_semaphore.get_info = AsyncMock(return_value={})
        
        # Mock bot.get_status_info() with base status
        base_status = {
            'version': '2025.11.15.5.2.0',
            'platform': 'Linux 5.15.0',
            'architecture': 'x86_64',
            'runtime': 'Python 3.12.0 (interpreter)',
            'metrics': {
                'messages_sent': 0,
                'requests_received': 0,
                'errors': 0,
                'emojis_used': 0
            },
            'matrix_status': 'Connected',
            'matrix_homeserver': 'https://matrix.example.com',
            'matrix_user_id': '@bot:example.com',
            'matrix_encrypted': False,
            'semaphore_status': 'Connected',
            'uptime': 0
        }
        self.mock_bot.get_status_info = MagicMock(return_value=base_status)
        
        # Mock bot client
        self.mock_bot.client = MagicMock()
        self.mock_bot.client.homeserver = 'https://matrix.example.com'
        self.mock_bot.client.user_id = '@bot:example.com'
        
        # Test without redact flag (should include IPs)
        # Recreate handler with redact=False in config
        self.config['redact'] = False
        handler_no_redact = CommandHandler(
            bot=self.mock_bot,
            config=self.config,
            semaphore=self.mock_semaphore
        )
        
        self.loop.run_until_complete(
            handler_no_redact.get_semaphore_info('!test:example.com', '@user:example.com')
        )
        
        call_args1 = self.mock_bot.send_message.call_args[0]
        message1 = call_args1[1]
        # May or may not have hostname depending on system, but structure should be there
        self.assertIn('ChatrixCD Bot', message1)
        
        # Reset mock
        self.mock_bot.send_message.reset_mock()
        
        # Test with redact flag (should not include IPs)
        # Recreate handler with redact=True in config
        self.config['redact'] = True
        handler_redact = CommandHandler(
            bot=self.mock_bot,
            config=self.config,
            semaphore=self.mock_semaphore
        )
        
        self.loop.run_until_complete(
            handler_redact.get_semaphore_info('!test:example.com', '@user:example.com')
        )
        
        call_args2 = self.mock_bot.send_message.call_args[0]
        message2 = call_args2[1]
        # Should not include Hostname or IPv4/IPv6 sections
        self.assertNotIn('Hostname:', message2)
        self.assertNotIn('IPv4:', message2)
        self.assertNotIn('IPv6:', message2)

    def test_verify_command_no_args(self):
        """Test verify command with no arguments."""
        self.loop.run_until_complete(
            self.handler.verify_device('!room:example.com', '@user:example.com', [])
        )
        
        # Should send help message
        self.assertEqual(self.mock_bot.send_message.call_count, 1)
        call_args = self.mock_bot.send_message.call_args[0]
        message = call_args[1]
        self.assertIn('Device Verification Options', message)
        self.assertIn('verify list', message)

    def test_verify_command_list(self):
        """Test verify list command."""
        # Mock verification manager
        self.mock_bot.verification_manager = MagicMock()
        self.mock_bot.verification_manager.get_unverified_devices = AsyncMock(return_value=[
            {'user_id': '@bot:example.com', 'device_id': 'DEVICE1', 'device_name': 'Bot Device'}
        ])
        
        self.loop.run_until_complete(
            self.handler.verify_device('!room:example.com', '@user:example.com', ['list'])
        )
        
        # Should call get_unverified_devices and send message
        self.mock_bot.verification_manager.get_unverified_devices.assert_called_once()
        self.assertEqual(self.mock_bot.send_message.call_count, 1)

    def test_verify_command_start(self):
        """Test verify start command."""
        # Mock verification manager
        self.mock_bot.verification_manager = MagicMock()
        self.mock_bot.verification_manager.get_unverified_devices = AsyncMock(return_value=[
            {'user_id': '@bot:example.com', 'device_id': 'DEVICE1', 'device': MagicMock()}
        ])
        self.mock_bot.verification_manager.start_verification = AsyncMock(return_value=MagicMock())
        
        self.loop.run_until_complete(
            self.handler.verify_device('!room:example.com', '@user:example.com',
                                     ['start', '@bot:example.com', 'DEVICE1'])
        )
        
        # Should call start_verification and send message
        self.mock_bot.verification_manager.start_verification.assert_called_once()
        self.assertEqual(self.mock_bot.send_message.call_count, 1)

    def test_sessions_command_no_args(self):
        """Test sessions command with no arguments."""
        self.loop.run_until_complete(
            self.handler.manage_sessions('!room:example.com', '@user:example.com', [])
        )
        
        # Should send help message
        self.assertEqual(self.mock_bot.send_message.call_count, 1)
        call_args = self.mock_bot.send_message.call_args[0]
        message = call_args[1]
        self.assertIn('Session Management', message)
        self.assertIn('sessions list', message)

    def test_sessions_command_list(self):
        """Test sessions list command."""
        # Mock verification manager
        self.mock_bot.verification_manager = MagicMock()
        self.mock_bot.verification_manager.get_verified_devices = AsyncMock(return_value=[
            {'user_id': '@bot:example.com', 'device_id': 'DEVICE1', 'device_name': 'Bot Device'}
        ])
        self.mock_bot.verification_manager.get_unverified_devices = AsyncMock(return_value=[])
        
        self.loop.run_until_complete(
            self.handler.manage_sessions('!room:example.com', '@user:example.com', ['list'])
        )
        
        # Should call device listing methods and send message
        self.mock_bot.verification_manager.get_verified_devices.assert_called_once()
        self.mock_bot.verification_manager.get_unverified_devices.assert_called_once()
        self.assertEqual(self.mock_bot.send_message.call_count, 1)

    @unittest.skipIf(not SAS_AVAILABLE, "Sas not available in this nio version")
    def test_cross_verify_bots(self):
        """Test cross verification with other bots."""
        # Mock room with multiple users
        mock_room = MagicMock()
        mock_room.users = ['@user:example.com', '@sparkles:example.com', '@opsbot:example.com']
        mock_room.encrypted = True
        
        # Create real verification manager with mock client
        from chatrixcd.verification import DeviceVerificationManager
        mock_client = MagicMock()
        mock_client.olm = MagicMock()
        mock_client.user_id = "@bot:example.com"
        mock_client.device_id = "BOTDEVICE"
        verification_manager = DeviceVerificationManager(mock_client)
        
        # Mock the methods used by cross_verify_with_bots
        verification_manager.get_unverified_devices = AsyncMock(return_value=[
            {'user_id': '@sparkles:example.com', 'device_id': 'DEVICE1', 'device': MagicMock()}
        ])
        verification_manager.start_verification = AsyncMock(return_value=MagicMock())
        
        self.mock_bot.verification_manager = verification_manager
        
        # Mock client.rooms
        self.mock_bot.client = MagicMock()
        self.mock_bot.client.rooms = {'!room:example.com': mock_room}
        
        self.loop.run_until_complete(
            self.handler._cross_verify_bots('!room:example.com', '@user:example.com')
        )
        
        # Should attempt to start verification with bot devices
        verification_manager.start_verification.assert_called_once()
        self.assertEqual(self.mock_bot.send_message.call_count, 2)  # Initial message + result


if __name__ == '__main__':
    unittest.main()
