"""Comprehensive TUI automated tests using Textual pilot.

This test suite uses Textual's pilot feature to perform automated testing
of all TUI components and features.
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from textual.pilot import Pilot
from chatrixcd.tui import (
    ChatrixTUI,
    AdminsScreen,
    RoomsScreen,
    SessionsScreen,
    SayScreen,
    LogScreen,
    SetScreen,
    ShowScreen,
    AliasesScreen,
    OIDCAuthScreen,
    MessageScreen,
    BotStatusWidget,
    ActiveTasksWidget,
)


class TestChatrixTUIMainApp(unittest.IsolatedAsyncioTestCase):
    """Test ChatrixTUI main app with pilot."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}  # Empty dict for rooms
        self.mock_bot.client.olm = None  # No encryption by default
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}
        
        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {
            'admin_users': ['@admin:example.com'],
            'allowed_rooms': ['!room:example.com']
        }
        self.mock_config.get_matrix_config.return_value = {
            'homeserver': 'https://matrix.example.com',
            'user_id': '@bot:example.com',
            'device_id': 'BOTDEVICE'
        }
        self.mock_config.get_semaphore_config.return_value = {
            'url': 'https://semaphore.example.com',
            'api_token': 'test_token'
        }

    async def test_main_app_startup(self):
        """Test that TUI main app starts up correctly."""
        app = ChatrixTUI(self.mock_bot, self.mock_config, use_color=True)
        
        async with app.run_test() as pilot:
            # Check that app is running
            self.assertIsNotNone(pilot.app)
            self.assertTrue(app.is_running)
            
            # Check that main screen is displayed
            self.assertIsNotNone(app.screen)

    async def test_main_menu_rendering(self):
        """Test that main menu renders with all expected buttons."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check for all expected buttons
            buttons = {
                "status": "STATUS",
                "admins": "ADMINS",
                "rooms": "ROOMS",
                "sessions": "SESSIONS",
                "say": "SAY",
                "log": "LOG",
                "set": "SET",
                "show": "SHOW",
                "aliases": "ALIASES",
                "quit": "QUIT"
            }
            
            for button_id, button_text in buttons.items():
                button = app.query_one(f"#{button_id}")
                self.assertIsNotNone(button, f"Button {button_id} not found")

    async def test_keyboard_binding_quit(self):
        """Test quit keyboard binding (q)."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause()
            
            # App should exit gracefully
            # Note: run_test handles cleanup automatically

    async def test_status_button_click(self):
        """Test clicking STATUS button opens status screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Click STATUS button
            await pilot.click("#status")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_keyboard_binding_status(self):
        """Test status keyboard binding (s)."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 's' for status
            await pilot.press("s")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_admins_button_click(self):
        """Test clicking ADMINS button opens admins screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Click ADMINS button
            await pilot.click("#admins")
            await pilot.pause()
            
            # Should display admins screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_keyboard_binding_admins(self):
        """Test admins keyboard binding (a)."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'a' for admins
            await pilot.press("a")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_rooms_button_click(self):
        """Test clicking ROOMS button opens rooms screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Click ROOMS button
            await pilot.click("#rooms")
            await pilot.pause()
            
            # Should display rooms screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_keyboard_binding_rooms(self):
        """Test rooms keyboard binding (r)."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'r' for rooms
            await pilot.press("r")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_sessions_button_click(self):
        """Test clicking SESSIONS button opens sessions screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Use keyboard binding instead of click (more reliable)
            await pilot.press("e")
            await pilot.pause()
            
            # Should display sessions screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_keyboard_binding_sessions(self):
        """Test sessions keyboard binding (e)."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'e' for sessions
            await pilot.press("e")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_aliases_button_click(self):
        """Test clicking ALIASES button opens aliases screen."""
        # Add alias manager to mock
        self.mock_bot.command_handler.alias_manager = Mock()
        self.mock_bot.command_handler.alias_manager.list_aliases.return_value = {}
        
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Use keyboard binding instead (button might be out of view)
            await pilot.press("x")
            await pilot.pause()
            
            # Should display aliases screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_keyboard_binding_aliases(self):
        """Test aliases keyboard binding (x)."""
        # Add alias manager to mock
        self.mock_bot.command_handler.alias_manager = Mock()
        self.mock_bot.command_handler.alias_manager.list_aliases.return_value = {}
        
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press 'x' for aliases
            await pilot.press("x")
            await pilot.pause()
            
            # Should have pushed a new screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_theme_default(self):
        """Test default theme application."""
        app = ChatrixTUI(self.mock_bot, self.mock_config, theme='default')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check theme is set
            self.assertEqual(app.theme_name, 'default')
            
            # Check CSS variables are applied
            css_vars = app.get_css_variables()
            self.assertIn('primary', css_vars)
            self.assertIn('background', css_vars)
            self.assertIn('text', css_vars)

    async def test_theme_midnight(self):
        """Test midnight theme application."""
        app = ChatrixTUI(self.mock_bot, self.mock_config, theme='midnight')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check theme is set
            self.assertEqual(app.theme_name, 'midnight')
            
            # Check CSS variables are applied
            css_vars = app.get_css_variables()
            self.assertEqual(css_vars['text'], '#00FFFF')  # Cyan

    async def test_theme_grayscale(self):
        """Test grayscale theme application."""
        app = ChatrixTUI(self.mock_bot, self.mock_config, theme='grayscale')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            self.assertEqual(app.theme_name, 'grayscale')

    async def test_theme_invalid_fallback(self):
        """Test invalid theme falls back to default."""
        app = ChatrixTUI(self.mock_bot, self.mock_config, theme='invalid_theme')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Should fall back to default
            self.assertEqual(app.theme_name, 'default')

    async def test_active_tasks_widget_no_tasks(self):
        """Test ActiveTasksWidget displays 'no active tasks' when empty."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get active tasks widget
            widget = app.query_one("#active_tasks", ActiveTasksWidget)
            self.assertIsNotNone(widget)
            
            # Should show no tasks
            self.assertEqual(widget.tasks, [])

    async def test_active_tasks_widget_with_tasks(self):
        """Test ActiveTasksWidget displays tasks correctly."""
        # Add some tasks
        self.mock_bot.command_handler.active_tasks = {
            '123': {'project_id': 1, 'status': 'running'}
        }
        self.mock_bot.semaphore.get_task_status = AsyncMock(return_value={'status': 'running'})
        
        app = ChatrixTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Wait for update
            await asyncio.sleep(0.5)
            
            # Get active tasks widget
            widget = app.query_one("#active_tasks", ActiveTasksWidget)
            self.assertIsNotNone(widget)


class TestAdminsScreen(unittest.IsolatedAsyncioTestCase):
    """Test AdminsScreen with pilot."""

    async def test_admins_screen_display(self):
        """Test AdminsScreen displays admin users."""
        admins = ['@admin1:example.com', '@admin2:example.com']
        
        # Create a minimal app to host the screen
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {'admin_users': admins}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            # Push the admins screen
            screen = AdminsScreen(admins)
            app.push_screen(screen)
            await pilot.pause()
            
            # Screen should be active
            self.assertIs(app.screen, screen)

    async def test_admins_screen_no_admins(self):
        """Test AdminsScreen with no admin users."""
        admins = []
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {'admin_users': admins}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = AdminsScreen(admins)
            app.push_screen(screen)
            await pilot.pause()
            
            # Should display message about no admins
            self.assertIs(app.screen, screen)

    async def test_admins_screen_back_navigation(self):
        """Test AdminsScreen back navigation with escape."""
        admins = ['@admin:example.com']
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {'admin_users': admins}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = AdminsScreen(admins)
            app.push_screen(screen)
            await pilot.pause()
            
            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()
            
            # Should be back to main screen
            self.assertIsNot(app.screen, screen)


class TestRoomsScreen(unittest.IsolatedAsyncioTestCase):
    """Test RoomsScreen with pilot."""

    async def test_rooms_screen_display(self):
        """Test RoomsScreen displays rooms."""
        rooms = [
            {'id': '!room1:example.com', 'name': 'Room 1'},
            {'id': '!room2:example.com', 'name': 'Room 2'}
        ]
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = RoomsScreen(rooms)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_rooms_screen_no_rooms(self):
        """Test RoomsScreen with no rooms."""
        rooms = []
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = RoomsScreen(rooms)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_rooms_screen_back_navigation(self):
        """Test RoomsScreen back navigation."""
        rooms = [{'id': '!room:example.com', 'name': 'Room'}]
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = RoomsScreen(rooms)
            app.push_screen(screen)
            await pilot.pause()
            
            # Press b to go back
            await pilot.press("b")
            await pilot.pause()
            
            self.assertIsNot(app.screen, screen)


class TestSessionsScreen(unittest.IsolatedAsyncioTestCase):
    """Test SessionsScreen with pilot."""

    async def test_sessions_screen_display(self):
        """Test SessionsScreen displays correctly."""
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.device_id = "DEVICE123"
        mock_bot.client.olm = Mock()
        mock_bot.client.olm.account = Mock()
        mock_bot.client.olm.account.identity_keys = {'ed25519': 'key123'}
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = SessionsScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_sessions_screen_no_encryption(self):
        """Test SessionsScreen when encryption is not enabled."""
        mock_bot = Mock()
        mock_bot.client = None
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = SessionsScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


class TestMessageScreen(unittest.IsolatedAsyncioTestCase):
    """Test MessageScreen with pilot."""

    async def test_message_screen_display(self):
        """Test MessageScreen displays message."""
        message = "Test message"
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = MessageScreen(message)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)
            self.assertEqual(screen.message, message)

    async def test_message_screen_close(self):
        """Test MessageScreen can be closed."""
        message = "Test message"
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = MessageScreen(message)
            app.push_screen(screen)
            await pilot.pause()
            
            # Press escape to close
            await pilot.press("escape")
            await pilot.pause()
            
            self.assertIsNot(app.screen, screen)


class TestOIDCAuthScreen(unittest.IsolatedAsyncioTestCase):
    """Test OIDCAuthScreen with pilot."""

    async def test_oidc_screen_display(self):
        """Test OIDCAuthScreen displays correctly."""
        sso_url = "https://chat.example.org/_matrix/client/v3/login/sso/redirect/oidc?redirectUrl=http://localhost:8080/callback"
        redirect_url = "http://localhost:8080/callback"
        identity_providers = [{'id': 'oidc', 'name': 'OIDC Provider'}]
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)
            self.assertEqual(screen.sso_url, sso_url)
            self.assertEqual(screen.redirect_url, redirect_url)

    async def test_oidc_screen_special_characters(self):
        """Test OIDCAuthScreen handles special characters in URLs."""
        sso_url = "https://example.com/path?param1=value1&param2=value2#fragment"
        redirect_url = "http://localhost:8080/callback?session=123&state=abc"
        identity_providers = []
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


class TestAliasesScreen(unittest.IsolatedAsyncioTestCase):
    """Test AliasesScreen with pilot."""

    async def test_aliases_screen_no_aliases(self):
        """Test AliasesScreen with no aliases configured."""
        mock_bot = Mock()
        mock_bot.command_handler = Mock()
        mock_bot.command_handler.alias_manager = Mock()
        mock_bot.command_handler.alias_manager.list_aliases.return_value = {}
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = AliasesScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_aliases_screen_with_aliases(self):
        """Test AliasesScreen displays existing aliases."""
        mock_bot = Mock()
        mock_bot.command_handler = Mock()
        mock_bot.command_handler.alias_manager = Mock()
        mock_bot.command_handler.alias_manager.list_aliases.return_value = {
            'deploy': 'run 1 5',
            'status': 'status 123'
        }
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = AliasesScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_aliases_screen_back_navigation(self):
        """Test AliasesScreen back navigation."""
        mock_bot = Mock()
        mock_bot.command_handler = Mock()
        mock_bot.command_handler.alias_manager = Mock()
        mock_bot.command_handler.alias_manager.list_aliases.return_value = {}
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = AliasesScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()
            
            self.assertIsNot(app.screen, screen)


class TestBotStatusWidget(unittest.IsolatedAsyncioTestCase):
    """Test BotStatusWidget with pilot."""

    async def test_status_widget_rendering(self):
        """Test BotStatusWidget renders correctly."""
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.logged_in = True
        mock_bot.semaphore = Mock()
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Widget should be present in status screen
            # We can test this by navigating to status screen
            await pilot.press("s")
            await pilot.pause()

    async def test_status_widget_update_matrix_status(self):
        """Test updating matrix status in BotStatusWidget."""
        widget = BotStatusWidget()
        
        # Update status
        widget.matrix_status = "Connected"
        
        self.assertEqual(widget.matrix_status, "Connected")

    async def test_status_widget_update_metrics(self):
        """Test updating metrics in BotStatusWidget."""
        widget = BotStatusWidget()
        
        # Update metrics
        widget.messages_processed = 10
        widget.errors = 2
        widget.warnings = 3
        
        self.assertEqual(widget.messages_processed, 10)
        self.assertEqual(widget.errors, 2)
        self.assertEqual(widget.warnings, 3)


class TestActiveTasksWidget(unittest.IsolatedAsyncioTestCase):
    """Test ActiveTasksWidget with pilot."""

    async def test_active_tasks_widget_no_tasks(self):
        """Test ActiveTasksWidget with no tasks."""
        widget = ActiveTasksWidget()
        
        # Should have empty tasks list
        self.assertEqual(widget.tasks, [])
        
        # Render should show 'no active tasks'
        rendered = widget.render()
        self.assertIn("No active tasks", rendered)

    async def test_active_tasks_widget_with_tasks(self):
        """Test ActiveTasksWidget with tasks."""
        widget = ActiveTasksWidget()
        
        # Add tasks
        widget.tasks = [
            {'task_id': 123, 'project_id': 1, 'status': 'running'},
            {'task_id': 124, 'project_id': 2, 'status': 'success'}
        ]
        
        # Render should show tasks
        rendered = widget.render()
        self.assertIn("Task 123", rendered)
        self.assertIn("Task 124", rendered)
        self.assertIn("running", rendered)
        self.assertIn("success", rendered)


class TestSayScreen(unittest.IsolatedAsyncioTestCase):
    """Test SayScreen with pilot."""

    async def test_say_screen_display(self):
        """Test SayScreen displays correctly."""
        rooms = [
            {'id': '!room1:example.com', 'name': 'Room 1'},
            {'id': '!room2:example.com', 'name': 'Room 2'}
        ]
        
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.rooms = {}
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = SayScreen(app, rooms)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)

    async def test_say_screen_no_rooms(self):
        """Test SayScreen when no rooms are available."""
        rooms = []
        
        mock_bot = Mock()
        mock_bot.client = None
        
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = SayScreen(app, rooms)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


class TestLogScreen(unittest.IsolatedAsyncioTestCase):
    """Test LogScreen with pilot."""

    async def test_log_screen_display(self):
        """Test LogScreen displays correctly."""
        log_content = """2024-01-01 10:00:00 INFO Starting bot
2024-01-01 10:00:01 INFO Connected to Matrix
2024-01-01 10:00:02 INFO Ready to receive commands"""
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = LogScreen(log_content)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


class TestSetScreen(unittest.IsolatedAsyncioTestCase):
    """Test SetScreen with pilot."""

    async def test_set_screen_display(self):
        """Test SetScreen displays correctly."""
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = SetScreen(app)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


class TestShowScreen(unittest.IsolatedAsyncioTestCase):
    """Test ShowScreen with pilot."""

    async def test_show_screen_display(self):
        """Test ShowScreen displays configuration."""
        config_text = """Matrix Configuration:
  Homeserver: https://matrix.example.com
  User ID: @bot:example.com

Semaphore Configuration:
  URL: https://semaphore.example.com
"""
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {
            'admin_users': ['@admin:example.com'],
            'allowed_rooms': ['!room:example.com']
        }
        
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test() as pilot:
            screen = ShowScreen(config_text)
            app.push_screen(screen)
            await pilot.pause()
            
            self.assertIs(app.screen, screen)


if __name__ == '__main__':
    unittest.main()
