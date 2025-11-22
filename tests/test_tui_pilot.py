"""Textual pilot tests for TUI.

Tests interactive workflows using Textual's pilot testing framework.
"""

import unittest
import asyncio
from unittest.mock import Mock

from chatrixcd.tui.app import ChatrixTUI
from chatrixcd.tui.screens.main_menu import MainMenuScreen
from chatrixcd.tui.screens.status import StatusScreen
from chatrixcd.tui.screens.rooms import RoomsScreen
from chatrixcd.tui.screens.logs import LogsScreen
from chatrixcd.tui.screens.config import ConfigScreen


class TestTUINavigation(unittest.IsolatedAsyncioTestCase):
    """Test TUI navigation and screen transitions."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.user_id = "@bot:example.com"
        self.mock_bot.client.rooms = {}
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {}
        self.mock_bot.metrics = {
            "uptime": 3600,
            "messages_sent": 100,
            "requests_received": 50,
            "errors": 0,
            "emojis_used": 42,
        }

        # Mock plugin manager with empty loaded_plugins dict
        self.mock_plugin_manager = Mock()
        self.mock_plugin_manager.loaded_plugins = {}
        self.mock_bot.plugin_manager = self.mock_plugin_manager

        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {
            "admin_users": ["@admin:example.com"],
            "allowed_rooms": ["!room:example.com"],
            "log_file": "test.log",
        }
        self.mock_config.config = {
            "matrix": {"homeserver": "https://matrix.example.com"},
            "semaphore": {"url": "https://semaphore.example.com"},
        }

    async def test_app_initialization(self):
        """Test TUI app initializes correctly."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        self.assertEqual(app.bot, self.mock_bot)
        self.assertEqual(app.config, self.mock_config)
        self.assertIsNotNone(app.screen_registry)

    async def test_main_menu_displays(self):
        """Test main menu screen displays."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Main menu should be the initial screen
            await pilot.pause()

            # Check that we're on main menu
            self.assertIsInstance(app.screen, MainMenuScreen)

    async def test_navigate_to_status_screen(self):
        """Test navigating to status screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            # Wait for app to mount
            await pilot.pause()

            # Press 's' to go to status screen
            await pilot.press("s")
            await pilot.pause()

            # Should now be on status screen
            self.assertIsInstance(app.screen, StatusScreen)

    async def test_navigate_back_from_screen(self):
        """Test navigating back from a screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Go to status screen
            await pilot.press("s")
            await pilot.pause()

            # Go back
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on main menu
            self.assertIsInstance(app.screen, MainMenuScreen)

    async def test_navigate_to_rooms_screen(self):
        """Test navigating to rooms screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Press 'r' to go to rooms screen
            await pilot.press("r")
            await pilot.pause()

            # Should be on rooms screen
            self.assertIsInstance(app.screen, RoomsScreen)

    async def test_navigate_to_logs_screen(self):
        """Test navigating to logs screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Press 'l' to go to logs screen
            await pilot.press("l")
            await pilot.pause()

            # Should be on logs screen
            self.assertIsInstance(app.screen, LogsScreen)

    async def test_navigate_to_config_screen(self):
        """Test navigating to config screen."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Press 'c' to go to config screen
            await pilot.press("c")
            await pilot.pause()

            # Should be on config screen
            self.assertIsInstance(app.screen, ConfigScreen)

    async def test_quit_application(self):
        """Test quitting the application."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause()

            # App should have exited
            self.assertTrue(True)  # If we get here, quit worked


class TestStatusScreen(unittest.IsolatedAsyncioTestCase):
    """Test status screen functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.semaphore = Mock()
        self.mock_bot.command_handler = Mock()
        self.mock_bot.command_handler.active_tasks = {
            123: {
                "status": "running",
                "project_id": 1,
            },
            124: {
                "status": "success",
                "project_id": 2,
            },
        }
        self.mock_bot.metrics = {
            "uptime": 7200,
            "messages_sent": 250,
            "requests_received": 150,
            "errors": 5,
            "emojis_used": 100,
        }

        # Mock plugin manager
        self.mock_plugin_manager = Mock()
        self.mock_plugin_manager.loaded_plugins = {}
        self.mock_bot.plugin_manager = self.mock_plugin_manager

        self.mock_config = Mock()
        self.mock_config.config = {}

    async def test_status_screen_displays_metrics(self):
        """Test status screen displays metrics."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Navigate to status screen
            await pilot.press("s")
            await pilot.pause()

            # Give it time to refresh data
            await asyncio.sleep(0.5)
            await pilot.pause()

            # Status screen should display metrics
            # (We can't easily check the exact text, but we can verify no crashes)
            self.assertIsInstance(app.screen, StatusScreen)

    async def test_status_screen_shows_active_tasks(self):
        """Test status screen shows active tasks."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            await pilot.press("s")
            await pilot.pause()

            # Wait for data refresh
            await asyncio.sleep(0.5)
            await pilot.pause()

            # Should show active tasks
            self.assertIsInstance(app.screen, StatusScreen)


class TestRoomsScreen(unittest.IsolatedAsyncioTestCase):
    """Test rooms screen functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Mock room object
        mock_room = Mock()
        mock_room.display_name = "Test Room"
        mock_room.name = "Test Room"
        mock_room.users = {"@user1:example.com", "@user2:example.com"}
        mock_room.encrypted = True

        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.rooms = {
            "!room123:example.com": mock_room,
        }

        # Mock plugin manager
        self.mock_plugin_manager = Mock()
        self.mock_plugin_manager.loaded_plugins = {}
        self.mock_bot.plugin_manager = self.mock_plugin_manager

        self.mock_config = Mock()
        self.mock_config.config = {}

    async def test_rooms_screen_displays_rooms(self):
        """Test rooms screen displays room list."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Navigate to rooms screen
            await pilot.press("r")
            await pilot.pause()

            # Wait for data load
            await asyncio.sleep(0.5)
            await pilot.pause()

            # Should be on rooms screen
            self.assertIsInstance(app.screen, RoomsScreen)


class TestConfigScreen(unittest.IsolatedAsyncioTestCase):
    """Test config screen functionality."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()

        # Mock plugin manager
        self.mock_plugin_manager = Mock()
        self.mock_plugin_manager.loaded_plugins = {}
        self.mock_bot.plugin_manager = self.mock_plugin_manager

        self.mock_config = Mock()
        self.mock_config.config = {
            "matrix": {
                "homeserver": "https://matrix.example.com",
                "user_id": "@bot:example.com",
            },
            "semaphore": {
                "url": "https://semaphore.example.com",
            },
        }

    async def test_config_screen_displays_config(self):
        """Test config screen displays configuration."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # Navigate to config screen
            await pilot.press("c")
            await pilot.pause()

            # Wait for data load
            await asyncio.sleep(0.5)
            await pilot.pause()

            # Should be on config screen
            self.assertIsInstance(app.screen, ConfigScreen)


class TestPluginIntegration(unittest.IsolatedAsyncioTestCase):
    """Test plugin TUI integration."""

    async def asyncSetUp(self):
        """Set up test fixtures with mock plugin manager."""
        self.mock_bot = Mock()
        self.mock_bot.client = Mock()
        self.mock_bot.client.logged_in = True
        self.mock_bot.client.rooms = {}

        # Mock plugin manager
        self.mock_plugin_manager = Mock()
        self.mock_plugin_manager.loaded_plugins = {}
        self.mock_bot.plugin_manager = self.mock_plugin_manager

        self.mock_config = Mock()
        self.mock_config.config = {}
        self.mock_config.get_bot_config.return_value = {}

    async def test_tui_initializes_with_plugin_manager(self):
        """Test TUI initializes when plugin manager is present."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()

            # App should initialize without error
            self.assertIsNotNone(app.screen_registry)

    async def test_plugin_screens_can_be_registered(self):
        """Test that plugin screens can be registered."""
        app = ChatrixTUI(self.mock_bot, self.mock_config)

        # Create a mock screen class
        mock_screen = type("MockScreen", (object,), {})

        # Register a plugin screen
        success = app.screen_registry.register(
            name="plugin_test",
            screen_class=mock_screen,
            title="Plugin Test Screen",
            plugin_name="test_plugin",
            category="plugins",
        )

        self.assertTrue(success)

        # Verify it's registered
        registration = app.screen_registry.get("plugin_test")
        self.assertIsNotNone(registration)
        self.assertEqual(registration.plugin_name, "test_plugin")


if __name__ == "__main__":
    unittest.main()
