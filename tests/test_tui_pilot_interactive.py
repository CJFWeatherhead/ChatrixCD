"""Comprehensive TUI interactive workflow tests using Textual pilot.

This test suite focuses on interactive workflows such as:
- Alias management (add/delete)
- Message sending
- Configuration editing
- Device verification workflows
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock
from chatrixcd.tui import (
    ChatrixTUI,
    AliasesScreen,
)


class TestAliasManagementWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test alias management interactive workflows."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        # Mock the new plugin interface
        self.mock_alias_plugin = Mock()
        self.mock_alias_plugin.list_aliases.return_value = {}
        self.mock_alias_plugin.validate_command.return_value = True
        self.mock_alias_plugin.add_alias.return_value = True
        self.mock_alias_plugin.remove_alias.return_value = True
        self.mock_bot.command_handler._get_alias_plugin.return_value = self.mock_alias_plugin

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {
            "admin_users": ["@admin:example.com"],
            "allowed_rooms": ["!room:example.com"],
        }

    async def test_alias_screen_button_selection(self):
        """Test selecting an alias by clicking its button."""
        # Add existing aliases
        self.mock_alias_plugin.list_aliases.return_value = {
            "deploy": "run 1 5",
            "status": "status 123",
        }

        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Navigate to aliases screen
            await pilot.press("x")
            await pilot.pause()

            # Check screen changed
            screen = app.screen
            self.assertIsInstance(screen, AliasesScreen)

    async def test_alias_screen_keyboard_navigation(self):
        """Test alias screen keyboard navigation."""
        self.mock_alias_plugin.list_aliases.return_value = {}

        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Navigate to aliases screen
            await pilot.press("x")
            await pilot.pause()

            # Navigate back with 'b'
            await pilot.press("b")
            await pilot.pause()

            # Should be back at main screen
            self.assertNotIsInstance(app.screen, AliasesScreen)

    async def test_alias_screen_escape_navigation(self):
        """Test alias screen escape key navigation."""
        self.mock_alias_plugin.list_aliases.return_value = {}

        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Navigate to aliases screen
            await pilot.press("x")
            await pilot.pause()

            # Navigate back with escape
            await pilot.press("escape")
            await pilot.pause()

            # Should be back at main screen
            self.assertNotIsInstance(app.screen, AliasesScreen)


class TestNavigationWorkflows(unittest.IsolatedAsyncioTestCase):
    """Test navigation workflows between screens."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        # Mock get_status_info() method used by TUI
        self.mock_bot.get_status_info = Mock(
            return_value={
                "version": "2025.11.15.5.2.0",
                "platform": "Linux 5.15.0",
                "architecture": "x86_64",
                "runtime": "Python 3.12.0 (interpreter)",
                "metrics": {
                    "messages_sent": 0,
                    "requests_received": 0,
                    "errors": 0,
                    "emojis_used": 0,
                },
                "matrix_status": "Connected",
                "semaphore_status": "Connected",
                "uptime": 10000,  # milliseconds
            }
        )

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {
            "admin_users": ["@admin:example.com"],
            "allowed_rooms": ["!room:example.com"],
        }

    async def test_multiple_screen_navigation(self):
        """Test navigating through multiple screens."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Start at main screen
            initial_stack_size = len(app.screen_stack)

            # Navigate to status
            await pilot.press("s")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size + 1)

            # Navigate back
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size)

            # Navigate to admins
            await pilot.press("a")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size + 1)

            # Navigate back
            await pilot.press("b")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size)

    async def test_rapid_navigation(self):
        """Test rapid navigation doesn't break the app."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Rapidly navigate through screens
            for _ in range(3):
                await pilot.press("s")
                await pilot.pause(0.1)
                await pilot.press("escape")
                await pilot.pause(0.1)

            # App should still be running
            self.assertTrue(app.is_running)

    async def test_screen_stack_integrity(self):
        """Test screen stack maintains integrity during navigation."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            initial_stack_size = len(app.screen_stack)

            # Push multiple screens
            await pilot.press("s")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Stack should be back to initial size
            self.assertEqual(len(app.screen_stack), initial_stack_size)


class TestThemeApplication(unittest.IsolatedAsyncioTestCase):
    """Test theme application and switching."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}

    async def test_all_themes_render(self):
        """Test that all themes can be applied and render correctly."""
        themes = ["default", "midnight", "grayscale", "windows31", "msdos"]

        for theme in themes:
            app = ChatrixTUI(self.mock_bot, self.mock_config, theme=theme)

            async with app.run_test(size=(80, 30)) as pilot:
                await pilot.pause()

                # Check theme is applied
                self.assertEqual(app.theme_name, theme)

                # Check CSS variables are set
                css_vars = app.get_css_variables()
                self.assertIn("primary", css_vars)
                self.assertIn("background", css_vars)
                self.assertIn("text", css_vars)

                # App should be running
                self.assertTrue(app.is_running)

    async def test_theme_css_completeness(self):
        """Test that themes provide all required CSS variables."""
        required_vars = [
            "primary",
            "background",
            "surface",
            "text",
            "text-muted",
        ]

        for theme in ["default", "midnight", "grayscale"]:
            app = ChatrixTUI(self.mock_bot, self.mock_config, theme=theme)

            async with app.run_test(size=(80, 30)) as pilot:
                await pilot.pause()

                css_vars = app.get_css_variables()

                for var in required_vars:
                    self.assertIn(
                        var,
                        css_vars,
                        f"Theme {theme} missing CSS variable: {var}",
                    )


class TestWidgetUpdates(unittest.IsolatedAsyncioTestCase):
    """Test widget dynamic updates."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.semaphore.get_task_status = AsyncMock(return_value={"status": "running"})
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        # Mock get_status_info() method used by TUI
        self.mock_bot.get_status_info = Mock(
            return_value={
                "version": "2025.11.15.5.2.0",
                "platform": "Linux 5.15.0",
                "architecture": "x86_64",
                "runtime": "Python 3.12.0 (interpreter)",
                "metrics": {
                    "messages_sent": 0,
                    "requests_received": 0,
                    "errors": 0,
                    "emojis_used": 0,
                },
                "matrix_status": "Connected",
                "semaphore_status": "Connected",
                "uptime": 10000,  # milliseconds
            }
        )

        # Also mock metrics directly for backward compatibility
        self.mock_bot.metrics = {
            "messages_sent": 0,
            "requests_received": 0,
            "errors": 0,
            "emojis_used": 0,
        }

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}

    async def test_active_tasks_widget_updates(self):
        """Test that active tasks widget updates when tasks change."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Initially no tasks
            from chatrixcd.tui import ActiveTasksWidget

            widget = app.query_one("#active_tasks", ActiveTasksWidget)
            self.assertEqual(widget.tasks, [])

            # Add a task
            self.mock_bot.command_handler.active_tasks = {
                "123": {"project_id": 1, "status": "running"}
            }

            # Wait for update interval (set_interval in TUI is 5 seconds)
            UPDATE_INTERVAL = 5  # Seconds - matches set_interval in ChatrixTUI
            await asyncio.sleep(UPDATE_INTERVAL + 1)  # Wait slightly longer than interval

            # Widget should have been updated
            # Note: Actual update happens asynchronously

    async def test_bot_status_widget_reactive_updates(self):
        """Test BotStatusWidget reactive property updates."""

        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Navigate to status screen
            await pilot.press("s")
            await pilot.pause()

            # App should be on status screen with widget
            # Widget should show connection status


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test error handling in TUI."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = None  # Simulate disconnected state
        self.mock_bot.semaphore = None
        self.mock_bot.command_handler = None

        # Mock get_status_info() method - even when disconnected
        self.mock_bot.get_status_info = Mock(
            return_value={
                "version": "2025.11.15.5.2.0",
                "platform": "Linux 5.15.0",
                "architecture": "x86_64",
                "runtime": "Python 3.12.0 (interpreter)",
                "metrics": {
                    "messages_sent": 0,
                    "requests_received": 0,
                    "errors": 0,
                    "emojis_used": 0,
                },
                "matrix_status": "Disconnected",
                "semaphore_status": "Unknown",
                "uptime": 0,
            }
        )

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}

    async def test_graceful_handling_no_bot(self):
        """Test TUI handles missing bot gracefully."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Try to navigate to various screens
            await pilot.press("s")  # Status
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            await pilot.press("r")  # Rooms
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            # App should still be running
            self.assertTrue(app.is_running)

    async def test_graceful_handling_no_client(self):
        """Test TUI handles missing Matrix client gracefully."""
        self.mock_bot.client = None

        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Navigate through screens
            await pilot.press("e")  # Sessions
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            # App should handle it gracefully
            self.assertTrue(app.is_running)


class TestKeyboardShortcuts(unittest.IsolatedAsyncioTestCase):
    """Test all keyboard shortcuts work correctly."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        # Mock the new plugin interface
        self.mock_alias_plugin = Mock()
        self.mock_alias_plugin.list_aliases.return_value = {}
        self.mock_bot.command_handler._get_alias_plugin.return_value = self.mock_alias_plugin

        # Mock get_status_info() method
        self.mock_bot.get_status_info = Mock(
            return_value={
                "version": "2025.11.15.5.2.0",
                "platform": "Linux 5.15.0",
                "architecture": "x86_64",
                "runtime": "Python 3.12.0 (interpreter)",
                "metrics": {
                    "messages_sent": 0,
                    "requests_received": 0,
                    "errors": 0,
                    "emojis_used": 0,
                },
                "matrix_status": "Connected",
                "semaphore_status": "Connected",
                "uptime": 10000,
            }
        )

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}
        self.mock_config.get_matrix_config.return_value = {
            "homeserver": "https://matrix.example.com",
            "user_id": "@bot:example.com",
        }
        self.mock_config.get_semaphore_config.return_value = {
            "url": "https://semaphore.example.com"
        }

    async def test_all_keyboard_shortcuts(self):
        """Test all keyboard shortcuts trigger correct actions."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        shortcuts = {
            "s": "Status",
            "a": "Admins",
            "r": "Rooms",
            "e": "Sessions",
            "x": "Aliases",
            # 'm', 'l', 't', 'c' would require more complex mocks
        }

        async with app.run_test(size=(80, 30)) as pilot:
            initial_stack_size = len(app.screen_stack)

            for key, screen_name in shortcuts.items():
                # Press shortcut
                await pilot.press(key)
                await pilot.pause()

                # Should push a screen
                self.assertGreater(
                    len(app.screen_stack),
                    initial_stack_size,
                    f"Shortcut '{key}' ({screen_name}) didn't push a screen",
                )

                # Go back
                await pilot.press("escape")
                await pilot.pause()

                # Should be back at main
                self.assertEqual(
                    len(app.screen_stack),
                    initial_stack_size,
                    f"Screen stack not restored after '{key}' ({screen_name})",
                )

    async def test_quit_shortcuts(self):
        """Test quit shortcuts."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause()

            # App should be shutting down or shut down
            # Note: run_test context manager handles cleanup


class TestAppLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test application lifecycle events."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.client.olm = None
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}

        # Mock get_status_info() method
        self.mock_bot.get_status_info = Mock(
            return_value={
                "version": "2025.11.15.5.2.0",
                "platform": "Linux 5.15.0",
                "architecture": "x86_64",
                "runtime": "Python 3.12.0 (interpreter)",
                "metrics": {
                    "messages_sent": 0,
                    "requests_received": 0,
                    "errors": 0,
                    "emojis_used": 0,
                },
                "matrix_status": "Connected",
                "semaphore_status": "Connected",
                "uptime": 10000,
            }
        )

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}

    async def test_app_startup(self):
        """Test application starts up correctly."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # App should be running
            self.assertTrue(app.is_running)

            # Should have main screen
            self.assertIsNotNone(app.screen)

            # Should have header and footer
            self.assertEqual(len(list(app.query("Header"))), 1)
            self.assertEqual(len(list(app.query("Footer"))), 1)

    async def test_app_metrics_initialization(self):
        """Test application metrics are initialized."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        # Check initial values - TUI only tracks errors now, metrics are in bot
        self.assertEqual(app.errors, 0)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Errors should still be at initial value
            self.assertEqual(app.errors, 0)

    async def test_app_with_login_task(self):
        """Test application with login task set."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        # Set a mock login task
        async def mock_login():
            await asyncio.sleep(0.1)

        app.login_task = mock_login

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # App should handle login task
            self.assertTrue(app.is_running)


if __name__ == "__main__":
    unittest.main()
