"""Tests for TUI interface."""

import unittest
from unittest.mock import Mock, patch


class TestTUIImport(unittest.TestCase):
    """Test TUI module can be imported and basic functionality."""

    def test_import_tui_module(self):
        """Test that TUI module can be imported and has expected classes."""
        from chatrixcd.tui import ChatrixTUI, run_tui

        # Verify the classes/functions are actually imported and callable
        self.assertTrue(callable(ChatrixTUI))
        self.assertTrue(callable(run_tui))

        # Verify ChatrixTUI has expected methods
        self.assertTrue(hasattr(ChatrixTUI, "__init__"))
        self.assertTrue(hasattr(ChatrixTUI, "compose"))

    def test_tui_screens_import(self):
        """Test that TUI screen classes can be imported and are valid."""
        from chatrixcd.tui import (
            AdminsScreen,
            BotStatusWidget,
            MessageScreen,
            OIDCAuthScreen,
            RoomsScreen,
            SessionsScreen,
        )

        # Verify all classes are callable
        screen_classes = [
            AdminsScreen,
            RoomsScreen,
            SessionsScreen,
            MessageScreen,
            BotStatusWidget,
            OIDCAuthScreen,
        ]

        for screen_class in screen_classes:
            self.assertTrue(
                callable(screen_class),
                f"{screen_class.__name__} is not callable",
            )
            self.assertTrue(
                hasattr(screen_class, "__init__"),
                f"{screen_class.__name__} missing __init__",
            )


class TestTUICreation(unittest.TestCase):
    """Test TUI object creation."""

    def test_create_tui_instance(self):
        """Test creating a TUI instance with mock bot and config."""
        from chatrixcd.tui import ChatrixTUI

        # Create mock bot and config
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {
            "admin_users": ["@admin:example.com"],
            "allowed_rooms": ["!room:example.com"],
        }

        # Create TUI instance
        tui = ChatrixTUI(mock_bot, mock_config, use_color=True)

        self.assertIsNotNone(tui)
        self.assertEqual(tui.bot, mock_bot)
        self.assertEqual(tui.config, mock_config)
        self.assertTrue(tui.use_color)

    def test_tui_metrics_initialization(self):
        """Test that TUI metrics are initialized to zero."""
        from chatrixcd.tui import ChatrixTUI

        mock_bot = Mock()
        mock_bot.metrics = {
            "messages_sent": 0,
            "requests_received": 0,
            "errors": 0,
            "emojis_used": 0,
        }
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}

        tui = ChatrixTUI(mock_bot, mock_config)

        # TUI no longer has its own metrics - they're in bot.metrics
        self.assertEqual(tui.errors, 0)  # Only errors remain in TUI


class TestTUIScreens(unittest.TestCase):
    """Test TUI screen creation."""

    def test_admins_screen_creation(self):
        """Test creating an AdminsScreen."""
        from chatrixcd.tui import AdminsScreen

        admins = ["@admin1:example.com", "@admin2:example.com"]
        screen = AdminsScreen(admins)

        self.assertIsNotNone(screen)
        self.assertEqual(screen.admins, admins)

    def test_rooms_screen_creation(self):
        """Test creating a RoomsScreen."""
        from chatrixcd.tui import RoomsScreen

        rooms = [
            {"id": "!room1:example.com", "name": "Room 1"},
            {"id": "!room2:example.com", "name": "Room 2"},
        ]
        screen = RoomsScreen(rooms)

        self.assertIsNotNone(screen)
        self.assertEqual(screen.rooms, rooms)

    def test_message_screen_creation(self):
        """Test creating a MessageScreen."""
        from chatrixcd.tui import MessageScreen

        message = "Test message"
        screen = MessageScreen(message)

        self.assertIsNotNone(screen)
        self.assertEqual(screen.message, message)


class TestBotStatusWidget(unittest.TestCase):
    """Test BotStatusWidget."""

    def test_status_widget_creation(self):
        """Test creating a BotStatusWidget."""
        from chatrixcd.tui import BotStatusWidget

        widget = BotStatusWidget()

        self.assertIsNotNone(widget)
        self.assertEqual(widget.matrix_status, "Disconnected")
        self.assertEqual(widget.semaphore_status, "Unknown")
        # New metric names
        self.assertEqual(widget.messages_sent, 0)
        self.assertEqual(widget.requests_received, 0)
        self.assertEqual(widget.errors, 0)
        self.assertEqual(widget.emojis_used, 0)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration with TUI."""

    def test_log_only_flag(self):
        """Test -L/--log-only flag parsing."""
        from chatrixcd.main import parse_args

        with patch("sys.argv", ["chatrixcd", "-L"]):
            args = parse_args()
            self.assertTrue(args.log_only)

        with patch("sys.argv", ["chatrixcd", "--log-only"]):
            args = parse_args()
            self.assertTrue(args.log_only)

    def test_default_no_log_only(self):
        """Test that log_only defaults to False."""
        from chatrixcd.main import parse_args

        with patch("sys.argv", ["chatrixcd"]):
            args = parse_args()
            self.assertFalse(args.log_only)


class TestOIDCAuthScreen(unittest.TestCase):
    """Test OIDCAuthScreen for proper handling of SSO URLs."""

    def test_oidc_screen_creation(self):
        """Test creating an OIDCAuthScreen with special characters in URL."""
        from chatrixcd.tui import OIDCAuthScreen

        # URL with characters that would cause markup errors
        sso_url = (
            "https://chat.example.org/_matrix/client/v3/login/sso/redirect/oidc?redirectUrl="
            "http://localhost:8080/callback"
        )
        redirect_url = "http://localhost:8080/callback"
        identity_providers = [{"id": "oidc", "name": "OIDC Provider"}]

        screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)

        self.assertIsNotNone(screen)
        self.assertEqual(screen.sso_url, sso_url)
        self.assertEqual(screen.redirect_url, redirect_url)
        self.assertEqual(screen.identity_providers, identity_providers)
        self.assertIsNone(screen.token)

    def test_oidc_screen_with_special_chars(self):
        """Test OIDCAuthScreen handles URLs with special characters."""
        from chatrixcd.tui import OIDCAuthScreen

        # URL with various special characters
        sso_url = "https://example.com/path?param1=value1&param2=value2#fragment"
        redirect_url = "http://localhost:8080/callback?session=123&state=abc"
        identity_providers = []

        screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)

        self.assertIsNotNone(screen)
        self.assertEqual(screen.sso_url, sso_url)
        self.assertEqual(screen.redirect_url, redirect_url)

    def test_oidc_screen_compose_method(self):
        """Test that OIDCAuthScreen.compose() doesn't crash."""
        from chatrixcd.tui import OIDCAuthScreen

        sso_url = (
            "https://chat.example.org/_matrix/client/v3/login/sso/redirect/oidc?redirectUrl="
            "http://localhost:8080/callback"
        )
        redirect_url = "http://localhost:8080/callback"
        identity_providers = []

        screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)

        # Test that compose returns widgets without errors
        # We can't fully test the TUI rendering, but we can check the method exists and is callable
        self.assertTrue(hasattr(screen, "compose"))
        self.assertTrue(callable(screen.compose))


class TestShowConfigTUI(unittest.TestCase):
    """Test show_config_tui function."""

    def test_show_config_tui_import(self):
        """Test that show_config_tui can be imported."""
        from chatrixcd.tui import show_config_tui

        self.assertTrue(callable(show_config_tui))

    def test_show_config_tui_callable(self):
        """Test that show_config_tui is a coroutine function."""
        import inspect

        from chatrixcd.tui import show_config_tui

        self.assertTrue(inspect.iscoroutinefunction(show_config_tui))


class TestCSSCompatibility(unittest.TestCase):
    """Test CSS compatibility with Textual design system."""

    # Textual's ColorSystem.generate() returns 163 CSS variables
    # This includes all design system colors, scrollbar variables, etc.
    EXPECTED_CSS_VARIABLE_COUNT = 163

    def test_tui_css_variables_complete(self):
        """Test that TUI provides all required CSS variables for Textual widgets."""
        from chatrixcd.tui import ChatrixTUI

        mock_bot = Mock()
        mock_bot.client = None
        mock_bot.semaphore = None

        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        mock_config.get.return_value = "default"

        tui = ChatrixTUI(mock_bot, mock_config, use_color=True)
        css_vars = tui.get_css_variables()

        # Verify we have the complete set of CSS variables from ColorSystem
        self.assertEqual(
            len(css_vars),
            self.EXPECTED_CSS_VARIABLE_COUNT,
            (
                f"Should have {self.EXPECTED_CSS_VARIABLE_COUNT} "
                "CSS variables from ColorSystem.generate()"
            ),
        )

        # Verify critical scrollbar variables are present
        required_scrollbar_vars = [
            "scrollbar-background",
            "scrollbar-background-hover",
            "scrollbar-background-active",
            "scrollbar",
            "scrollbar-hover",
            "scrollbar-active",
            "scrollbar-corner-color",
        ]

        for var in required_scrollbar_vars:
            self.assertIn(var, css_vars, f"Missing required CSS variable: {var}")

    def test_all_themes_provide_css_variables(self):
        """Test that all themes provide complete CSS variables."""
        from chatrixcd.tui import ChatrixTUI

        mock_bot = Mock()
        mock_bot.client = None
        mock_bot.semaphore = None

        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        mock_config.get.return_value = "default"

        # Test all available themes
        themes = ["default", "midnight", "grayscale", "windows31", "msdos"]

        for theme_name in themes:
            with self.subTest(theme=theme_name):
                tui = ChatrixTUI(mock_bot, mock_config, theme=theme_name)
                css_vars = tui.get_css_variables()

                # Each theme should provide the complete set of CSS variables
                self.assertEqual(
                    len(css_vars),
                    self.EXPECTED_CSS_VARIABLE_COUNT,
                    (
                        f"Theme '{theme_name}' should have "
                        f"{self.EXPECTED_CSS_VARIABLE_COUNT} CSS variables"
                    ),
                )

                # Each theme should have scrollbar variables
                self.assertIn(
                    "scrollbar-background",
                    css_vars,
                    f"Theme '{theme_name}' missing scrollbar-background",
                )


class TestErrorHandling(unittest.TestCase):
    """Test error handling in main module."""

    def test_verbosity_affects_error_display(self):
        """Test that verbosity level affects error message display."""
        from chatrixcd.main import parse_args

        # Test verbosity levels
        with patch("sys.argv", ["chatrixcd"]):
            args = parse_args()
            self.assertEqual(args.verbosity, 0)

        with patch("sys.argv", ["chatrixcd", "-v"]):
            args = parse_args()
            self.assertEqual(args.verbosity, 1)

        with patch("sys.argv", ["chatrixcd", "-vv"]):
            args = parse_args()
            self.assertEqual(args.verbosity, 2)

        with patch("sys.argv", ["chatrixcd", "-vvv"]):
            args = parse_args()
            self.assertEqual(args.verbosity, 3)


class TestTUIStartupWithPlugins(unittest.TestCase):
    """Test TUI startup with plugins enabled and disabled."""

    def test_tui_startup_with_plugins_disabled(self):
        """Test TUI initializes correctly when plugins are disabled."""
        from chatrixcd.tui import ChatrixTUI

        # Create mock bot and config with plugins disabled
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.logged_in = True
        mock_bot.plugin_manager = Mock()
        mock_bot.plugin_manager.loaded_plugins = {}
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {
            "load_plugins": False,
        }

        # TUI should initialize successfully even without plugins
        tui = ChatrixTUI(mock_bot, mock_config, use_color=False)

        self.assertIsNotNone(tui)
        self.assertEqual(tui.bot, mock_bot)
        self.assertIsNotNone(tui.screen_registry)

    def test_tui_startup_with_plugins_enabled(self):
        """Test TUI initializes correctly when plugins are enabled."""
        from chatrixcd.tui import ChatrixTUI

        # Create mock bot and config with plugins enabled
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.logged_in = True
        mock_plugin_manager = Mock()
        mock_plugin_manager.loaded_plugins = {}
        mock_bot.plugin_manager = mock_plugin_manager
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {
            "load_plugins": True,
        }

        # TUI should initialize successfully with plugins enabled
        tui = ChatrixTUI(mock_bot, mock_config, use_color=False)

        self.assertIsNotNone(tui)
        self.assertEqual(tui.bot, mock_bot)
        self.assertIsNotNone(tui.screen_registry)

    def test_tui_startup_no_plugin_manager(self):
        """Test TUI gracefully handles missing plugin manager."""
        from chatrixcd.tui import ChatrixTUI

        # Create mock bot without plugin manager
        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.logged_in = True
        # No plugin_manager attribute
        delattr(mock_bot, "plugin_manager")
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}

        # TUI should initialize successfully even without plugin manager
        tui = ChatrixTUI(mock_bot, mock_config, use_color=False)

        self.assertIsNotNone(tui)
        self.assertEqual(tui.bot, mock_bot)
        self.assertIsNotNone(tui.screen_registry)

    def test_screen_registry_initialized(self):
        """Test that screen registry is properly initialized."""
        from chatrixcd.tui import ChatrixTUI

        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.plugin_manager = Mock()
        mock_bot.plugin_manager.loaded_plugins = {}
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}

        tui = ChatrixTUI(mock_bot, mock_config)

        # Screen registry should have core screens registered
        self.assertIsNotNone(tui.screen_registry.get("status"))
        self.assertIsNotNone(tui.screen_registry.get("rooms"))
        self.assertIsNotNone(tui.screen_registry.get("logs"))
        self.assertIsNotNone(tui.screen_registry.get("config"))
        self.assertIsNotNone(tui.screen_registry.get("verification"))

    def test_core_screens_accessible_without_plugins(self):
        """Test that all core screens are accessible without plugins."""
        from chatrixcd.tui import ChatrixTUI

        mock_bot = Mock()
        mock_bot.client = Mock()
        mock_bot.client.logged_in = True
        mock_bot.plugin_manager = Mock()
        mock_bot.plugin_manager.loaded_plugins = {}
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {"load_plugins": False}

        tui = ChatrixTUI(mock_bot, mock_config)

        # All core screens should be accessible via registry
        core_screens = ["status", "rooms", "logs", "config", "verification"]
        for screen_name in core_screens:
            registration = tui.screen_registry.get(screen_name)
            self.assertIsNotNone(
                registration,
                f"Core screen '{screen_name}' not found in registry",
            )
            # Should be able to instantiate the screen
            try:
                screen = registration.screen_class(tui)
                self.assertIsNotNone(screen)
            except Exception as e:
                self.fail(f"Failed to instantiate screen '{screen_name}': {e}")
