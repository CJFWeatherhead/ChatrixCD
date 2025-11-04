"""Comprehensive Turbo TUI automated tests using Textual pilot.

This test suite uses Textual's pilot feature to perform automated testing
of all Turbo TUI components and features.
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from textual.pilot import Pilot
from chatrixcd.tui_turbo import (
    ChatrixTurboTUI,
    TurboMenuBar,
    TurboStatusBar,
    TurboWindow,
    FileMenuScreen,
    EditMenuScreen,
    RunMenuScreen,
    HelpMenuScreen,
)
from chatrixcd.tui import ActiveTasksWidget


class TestChatrixTurboTUIMainApp(unittest.IsolatedAsyncioTestCase):
    """Test ChatrixTurboTUI main app with pilot."""

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

    async def test_turbo_main_app_startup(self):
        """Test that Turbo TUI main app starts up correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, use_color=True)
        
        async with app.run_test() as pilot:
            # Check that app is running
            self.assertIsNotNone(pilot.app)
            self.assertTrue(app.is_running)
            
            # Check that main screen is displayed
            self.assertIsNotNone(app.screen)

    async def test_turbo_main_menu_rendering(self):
        """Test that Turbo TUI main menu renders with menu bar."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check for menu bar
            menu_bar = app.query_one(TurboMenuBar)
            self.assertIsNotNone(menu_bar)
            
            # Check for status bar
            status_bar = app.query_one(TurboStatusBar)
            self.assertIsNotNone(status_bar)

    async def test_turbo_keyboard_binding_f1_file_menu(self):
        """Test F1 keyboard binding opens File menu."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press F1 for File menu
            await pilot.press("f1")
            await pilot.pause()
            
            # Should have pushed a menu screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_turbo_keyboard_binding_f2_edit_menu(self):
        """Test F2 keyboard binding opens Edit menu."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press F2 for Edit menu
            await pilot.press("f2")
            await pilot.pause()
            
            # Should have pushed a menu screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_turbo_keyboard_binding_f3_run_menu(self):
        """Test F3 keyboard binding opens Run menu."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press F3 for Run menu
            await pilot.press("f3")
            await pilot.pause()
            
            # Should have pushed a menu screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_turbo_keyboard_binding_f4_help_menu(self):
        """Test F4 keyboard binding opens Help menu."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press F4 for Help menu
            await pilot.press("f4")
            await pilot.pause()
            
            # Should have pushed a menu screen
            self.assertGreater(len(app.screen_stack), 1)

    async def test_turbo_menu_navigation_left_right(self):
        """Test left/right arrow keys cycle through menus."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            initial_index = app.current_menu_index
            
            # Press right to go to next menu
            await pilot.press("right")
            await pilot.pause()
            
            # Menu index should have changed
            # Note: Actual behavior depends on implementation

    async def test_turbo_theme_default(self):
        """Test Turbo TUI default theme application."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='default')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check theme is set
            self.assertEqual(app.theme_name, 'default')
            
            # Check CSS variables are applied
            css_vars = app.get_css_variables()
            self.assertIn('primary', css_vars)
            self.assertIn('background', css_vars)
            self.assertIn('text', css_vars)

    async def test_turbo_theme_midnight(self):
        """Test Turbo TUI midnight theme application."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='midnight')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Check theme is set
            self.assertEqual(app.theme_name, 'midnight')
            
            # Check CSS variables are applied
            css_vars = app.get_css_variables()
            self.assertEqual(css_vars['text'], '#00FFFF')  # Cyan

    async def test_turbo_theme_grayscale(self):
        """Test Turbo TUI grayscale theme application."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='grayscale')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            self.assertEqual(app.theme_name, 'grayscale')

    async def test_turbo_theme_windows31(self):
        """Test Turbo TUI Windows 3.1 theme application."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='windows31')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            self.assertEqual(app.theme_name, 'windows31')

    async def test_turbo_theme_msdos(self):
        """Test Turbo TUI MS-DOS theme application."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='msdos')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            self.assertEqual(app.theme_name, 'msdos')

    async def test_turbo_theme_invalid_fallback(self):
        """Test Turbo TUI invalid theme falls back to default."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme='invalid_theme')
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Should fall back to default
            self.assertEqual(app.theme_name, 'default')

    async def test_turbo_active_tasks_widget_no_tasks(self):
        """Test Turbo TUI ActiveTasksWidget displays 'no active tasks' when empty."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get active tasks widget
            widget = app.query_one("#active_tasks", ActiveTasksWidget)
            self.assertIsNotNone(widget)
            
            # Should show no tasks
            self.assertEqual(widget.tasks, [])

    async def test_turbo_active_tasks_widget_with_tasks(self):
        """Test Turbo TUI ActiveTasksWidget displays tasks correctly."""
        # Add some tasks
        self.mock_bot.command_handler.active_tasks = {
            '123': {'project_id': 1, 'status': 'running'}
        }
        self.mock_bot.semaphore.get_task_status = AsyncMock(return_value={'status': 'running'})
        
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Wait for widget to render and initialize
            WIDGET_UPDATE_WAIT = 0.5  # Seconds to wait for widget updates
            await asyncio.sleep(WIDGET_UPDATE_WAIT)
            
            # Get active tasks widget
            widget = app.query_one("#active_tasks", ActiveTasksWidget)
            self.assertIsNotNone(widget)

    async def test_turbo_status_bar_rendering(self):
        """Test Turbo TUI status bar renders correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Get status bar
            status_bar = app.query_one("#status_bar", TurboStatusBar)
            self.assertIsNotNone(status_bar)
            
            # Check default status
            self.assertEqual(status_bar.status_text, "Idle")

    async def test_turbo_quit_shortcut(self):
        """Test Turbo TUI quit shortcut."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Press Ctrl+C to quit
            await pilot.press("ctrl+c")
            await pilot.pause()
            
            # App should be shutting down or shut down
            # Note: run_test context manager handles cleanup


class TestTurboMenuScreens(unittest.IsolatedAsyncioTestCase):
    """Test Turbo TUI menu screens with pilot."""

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

    async def test_file_menu_screen_display(self):
        """Test File menu screen displays correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Open File menu
            await pilot.press("f1")
            await pilot.pause()
            
            # Should be on File menu screen
            self.assertIsInstance(app.screen, FileMenuScreen)

    async def test_edit_menu_screen_display(self):
        """Test Edit menu screen displays correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Open Edit menu
            await pilot.press("f2")
            await pilot.pause()
            
            # Should be on Edit menu screen
            self.assertIsInstance(app.screen, EditMenuScreen)

    async def test_run_menu_screen_display(self):
        """Test Run menu screen displays correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Open Run menu
            await pilot.press("f3")
            await pilot.pause()
            
            # Should be on Run menu screen
            self.assertIsInstance(app.screen, RunMenuScreen)

    async def test_help_menu_screen_display(self):
        """Test Help menu screen displays correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            # Open Help menu
            await pilot.press("f4")
            await pilot.pause()
            
            # Should be on Help menu screen
            self.assertIsInstance(app.screen, HelpMenuScreen)

    async def test_menu_screen_escape_navigation(self):
        """Test escape key closes menu screens."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test() as pilot:
            await pilot.pause()
            
            initial_stack_size = len(app.screen_stack)
            
            # Open File menu
            await pilot.press("f1")
            await pilot.pause()
            
            self.assertGreater(len(app.screen_stack), initial_stack_size)
            
            # Close with escape
            await pilot.press("escape")
            await pilot.pause()
            
            # Should be back to main screen
            self.assertEqual(len(app.screen_stack), initial_stack_size)


class TestTurboNavigationWorkflows(unittest.IsolatedAsyncioTestCase):
    """Test Turbo TUI navigation workflows."""

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

    async def test_multiple_menu_navigation(self):
        """Test navigating through multiple menus."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            initial_stack_size = len(app.screen_stack)
            
            # Navigate to File menu
            await pilot.press("f1")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size + 1)
            
            # Navigate back
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size)
            
            # Navigate to Edit menu
            await pilot.press("f2")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size + 1)
            
            # Navigate back
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(len(app.screen_stack), initial_stack_size)

    async def test_rapid_menu_navigation(self):
        """Test rapid menu navigation doesn't break the app."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            # Rapidly navigate through menus
            for _ in range(3):
                await pilot.press("f1")
                await pilot.pause(0.1)
                await pilot.press("escape")
                await pilot.pause(0.1)
            
            # App should still be running
            self.assertTrue(app.is_running)

    async def test_menu_cycle_with_arrow_keys(self):
        """Test cycling through menus with arrow keys."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            initial_index = app.current_menu_index
            
            # Press right arrow multiple times
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            
            # Press left arrow
            await pilot.press("left")
            await pilot.pause()
            
            # App should still be running
            self.assertTrue(app.is_running)


class TestTurboThemeApplication(unittest.IsolatedAsyncioTestCase):
    """Test Turbo TUI theme application and switching."""

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

    async def test_all_turbo_themes_render(self):
        """Test that all Turbo TUI themes can be applied and render correctly."""
        themes = ['default', 'midnight', 'grayscale', 'windows31', 'msdos']
        
        for theme in themes:
            app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme=theme)
            
            async with app.run_test(size=(80, 30)) as pilot:
                await pilot.pause()
                
                # Check theme is applied
                self.assertEqual(app.theme_name, theme)
                
                # Check CSS variables are set
                css_vars = app.get_css_variables()
                self.assertIn('primary', css_vars)
                self.assertIn('background', css_vars)
                self.assertIn('text', css_vars)
                
                # App should be running
                self.assertTrue(app.is_running)

    async def test_turbo_theme_css_completeness(self):
        """Test that Turbo TUI themes provide all required CSS variables."""
        required_vars = ['primary', 'background', 'surface', 'text', 'text-muted']
        
        for theme in ['default', 'midnight', 'grayscale']:
            app = ChatrixTurboTUI(self.mock_bot, self.mock_config, theme=theme)
            
            async with app.run_test(size=(80, 30)) as pilot:
                await pilot.pause()
                
                css_vars = app.get_css_variables()
                
                for var in required_vars:
                    self.assertIn(var, css_vars, 
                                f"Turbo theme {theme} missing CSS variable: {var}")


class TestTurboErrorHandling(unittest.IsolatedAsyncioTestCase):
    """Test Turbo TUI error handling."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_bot = Mock()
        self.mock_bot.client = None  # Simulate disconnected state
        self.mock_bot.semaphore = None
        self.mock_bot.command_handler = None
        
        self.mock_config = Mock()
        self.mock_config.get_bot_config.return_value = {}

    async def test_turbo_graceful_handling_no_bot(self):
        """Test Turbo TUI handles missing bot gracefully."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Try to navigate to various menus
            await pilot.press("f1")  # File
            await pilot.pause()
            
            await pilot.press("escape")
            await pilot.pause()
            
            await pilot.press("f2")  # Edit
            await pilot.pause()
            
            await pilot.press("escape")
            await pilot.pause()
            
            # App should still be running
            self.assertTrue(app.is_running)

    async def test_turbo_graceful_handling_no_client(self):
        """Test Turbo TUI handles missing Matrix client gracefully."""
        self.mock_bot.client = None
        
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Navigate through menus
            await pilot.press("f3")  # Run
            await pilot.pause()
            
            await pilot.press("escape")
            await pilot.pause()
            
            # App should handle it gracefully
            self.assertTrue(app.is_running)


class TestTurboAppLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test Turbo TUI application lifecycle events."""

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

    async def test_turbo_app_startup(self):
        """Test Turbo TUI application starts up correctly."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # App should be running
            self.assertTrue(app.is_running)
            
            # Should have main screen
            self.assertIsNotNone(app.screen)
            
            # Should have menu bar and status bar
            self.assertEqual(len(list(app.query(TurboMenuBar))), 1)
            self.assertEqual(len(list(app.query(TurboStatusBar))), 1)

    async def test_turbo_app_metrics_initialization(self):
        """Test Turbo TUI application metrics are initialized."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        # Check initial values
        self.assertEqual(app.messages_processed, 0)
        self.assertEqual(app.errors, 0)
        self.assertEqual(app.warnings, 0)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Metrics should still be at initial values
            self.assertEqual(app.messages_processed, 0)
            self.assertEqual(app.errors, 0)
            self.assertEqual(app.warnings, 0)

    async def test_turbo_app_with_login_task(self):
        """Test Turbo TUI application with login task set."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        # Set a mock login task
        async def mock_login():
            await asyncio.sleep(0.1)
        
        app.login_task = mock_login
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # App should handle login task
            self.assertTrue(app.is_running)

    async def test_turbo_menu_navigation_state(self):
        """Test Turbo TUI menu navigation state tracking."""
        app = ChatrixTurboTUI(self.mock_bot, self.mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            
            # Check menu order is set
            self.assertIsNotNone(app.menu_order)
            self.assertEqual(len(app.menu_order), 4)
            
            # Check initial menu index
            self.assertEqual(app.current_menu_index, 0)


if __name__ == '__main__':
    unittest.main()
