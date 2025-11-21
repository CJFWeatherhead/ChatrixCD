"""Comprehensive tests for TUI components.

Tests cover:
- Screen registry
- Event system
- Base widgets and screens
- Core screens
- Plugin integration
"""

import unittest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from chatrixcd.tui.registry import ScreenRegistry, ScreenRegistration
from chatrixcd.tui.events import (
    TUIEvent,
    ScreenChangeEvent,
    DataUpdateEvent,
    PluginLoadedEvent,
    NotificationEvent,
)
from chatrixcd.tui.screens.base import BaseScreen


class TestScreenRegistry(unittest.TestCase):
    """Test screen registry functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = ScreenRegistry()
        self.mock_screen_class = Mock()
        
    def test_register_screen(self):
        """Test registering a screen."""
        success = self.registry.register(
            name="test_screen",
            screen_class=self.mock_screen_class,
            title="Test Screen",
            key_binding="t",
            priority=10,
            category="test",
        )
        
        self.assertTrue(success)
        self.assertIn("test_screen", self.registry._screens)
        
    def test_register_duplicate_name(self):
        """Test registering screen with duplicate name fails."""
        self.registry.register(
            name="test_screen",
            screen_class=self.mock_screen_class,
            title="Test Screen",
        )
        
        # Try to register again with same name
        success = self.registry.register(
            name="test_screen",
            screen_class=Mock(),
            title="Another Screen",
        )
        
        self.assertFalse(success)
        
    def test_register_duplicate_key_binding(self):
        """Test registering with duplicate key binding removes it."""
        self.registry.register(
            name="screen1",
            screen_class=self.mock_screen_class,
            title="Screen 1",
            key_binding="t",
        )
        
        self.registry.register(
            name="screen2",
            screen_class=Mock(),
            title="Screen 2",
            key_binding="t",  # Duplicate key
        )
        
        # Second screen should register but without key binding
        reg = self.registry.get("screen2")
        self.assertIsNotNone(reg)
        self.assertIsNone(reg.key_binding)
        
    def test_unregister_screen(self):
        """Test unregistering a screen."""
        self.registry.register(
            name="test_screen",
            screen_class=self.mock_screen_class,
            title="Test Screen",
            key_binding="t",
        )
        
        success = self.registry.unregister("test_screen")
        self.assertTrue(success)
        self.assertNotIn("test_screen", self.registry._screens)
        self.assertNotIn("t", self.registry._key_bindings)
        
    def test_get_screen(self):
        """Test getting a screen by name."""
        self.registry.register(
            name="test_screen",
            screen_class=self.mock_screen_class,
            title="Test Screen",
        )
        
        registration = self.registry.get("test_screen")
        self.assertIsNotNone(registration)
        self.assertEqual(registration.name, "test_screen")
        self.assertEqual(registration.title, "Test Screen")
        
    def test_get_screen_by_key(self):
        """Test getting a screen by key binding."""
        self.registry.register(
            name="test_screen",
            screen_class=self.mock_screen_class,
            title="Test Screen",
            key_binding="t",
        )
        
        registration = self.registry.get_by_key("t")
        self.assertIsNotNone(registration)
        self.assertEqual(registration.name, "test_screen")
        
    def test_get_all_screens(self):
        """Test getting all screens."""
        self.registry.register(
            name="screen1",
            screen_class=self.mock_screen_class,
            title="Screen 1",
            priority=20,
        )
        self.registry.register(
            name="screen2",
            screen_class=Mock(),
            title="Screen 2",
            priority=10,
        )
        
        screens = self.registry.get_all()
        self.assertEqual(len(screens), 2)
        # Should be sorted by priority
        self.assertEqual(screens[0].name, "screen2")  # priority 10
        self.assertEqual(screens[1].name, "screen1")  # priority 20
        
    def test_get_screens_by_category(self):
        """Test filtering screens by category."""
        self.registry.register(
            name="core_screen",
            screen_class=self.mock_screen_class,
            title="Core Screen",
            category="core",
        )
        self.registry.register(
            name="plugin_screen",
            screen_class=Mock(),
            title="Plugin Screen",
            category="plugins",
        )
        
        core_screens = self.registry.get_all(category="core")
        self.assertEqual(len(core_screens), 1)
        self.assertEqual(core_screens[0].name, "core_screen")
        
    def test_screen_condition(self):
        """Test screen conditional visibility."""
        condition_met = Mock(return_value=True)
        condition_not_met = Mock(return_value=False)
        
        self.registry.register(
            name="visible_screen",
            screen_class=self.mock_screen_class,
            title="Visible Screen",
            condition=condition_met,
        )
        self.registry.register(
            name="hidden_screen",
            screen_class=Mock(),
            title="Hidden Screen",
            condition=condition_not_met,
        )
        
        screens = self.registry.get_all()
        self.assertEqual(len(screens), 1)
        self.assertEqual(screens[0].name, "visible_screen")
        
    def test_clear_plugin_screens(self):
        """Test removing all screens from a plugin."""
        self.registry.register(
            name="plugin_screen1",
            screen_class=self.mock_screen_class,
            title="Plugin Screen 1",
            plugin_name="test_plugin",
        )
        self.registry.register(
            name="plugin_screen2",
            screen_class=Mock(),
            title="Plugin Screen 2",
            plugin_name="test_plugin",
        )
        self.registry.register(
            name="core_screen",
            screen_class=Mock(),
            title="Core Screen",
        )
        
        removed = self.registry.clear_plugin_screens("test_plugin")
        self.assertEqual(removed, 2)
        self.assertEqual(len(self.registry.get_all()), 1)
        
    def test_get_categories(self):
        """Test getting list of categories."""
        self.registry.register(
            name="screen1",
            screen_class=self.mock_screen_class,
            title="Screen 1",
            category="core",
        )
        self.registry.register(
            name="screen2",
            screen_class=Mock(),
            title="Screen 2",
            category="plugins",
        )
        self.registry.register(
            name="screen3",
            screen_class=Mock(),
            title="Screen 3",
            category="core",
        )
        
        categories = self.registry.get_categories()
        self.assertEqual(set(categories), {"core", "plugins"})


class TestEvents(unittest.TestCase):
    """Test TUI events."""
    
    def test_tui_event(self):
        """Test base TUI event."""
        event = TUIEvent(source="test", data={"key": "value"})
        self.assertEqual(event.source, "test")
        self.assertEqual(event.data["key"], "value")
        
    def test_screen_change_event(self):
        """Test screen change event."""
        event = ScreenChangeEvent(
            screen_name="new_screen",
            previous_screen="old_screen"
        )
        self.assertEqual(event.screen_name, "new_screen")
        self.assertEqual(event.previous_screen, "old_screen")
        
    def test_data_update_event(self):
        """Test data update event."""
        data = {"status": "connected"}
        event = DataUpdateEvent(data_type="connection", data=data)
        self.assertEqual(event.data_type, "connection")
        self.assertEqual(event.data_payload, data)
        
    def test_plugin_loaded_event(self):
        """Test plugin loaded event."""
        event = PluginLoadedEvent(
            plugin_name="test_plugin",
            plugin_type="generic"
        )
        self.assertEqual(event.plugin_name, "test_plugin")
        self.assertEqual(event.plugin_type, "generic")
        
    def test_notification_event(self):
        """Test notification event."""
        event = NotificationEvent(message="Test notification", severity="warning")
        self.assertEqual(event.message, "Test notification")
        self.assertEqual(event.severity, "warning")


class TestBaseScreen(unittest.IsolatedAsyncioTestCase):
    """Test base screen functionality."""
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        self.mock_tui_app = Mock()
        self.mock_tui_app.bot = Mock()
        self.mock_tui_app.config = Mock()
        
    async def test_base_screen_initialization(self):
        """Test base screen initialization."""
        screen = BaseScreen(self.mock_tui_app)
        self.assertEqual(screen.tui_app, self.mock_tui_app)
        self.assertEqual(screen.SCREEN_TITLE, "Screen")
        
    async def test_refresh_data_hook(self):
        """Test refresh_data hook is called."""
        class TestScreen(BaseScreen):
            SCREEN_TITLE = "Test"
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.refresh_called = False
                
            async def refresh_data(self):
                self.refresh_called = True
                
        screen = TestScreen(self.mock_tui_app)
        await screen.refresh_data()
        self.assertTrue(screen.refresh_called)


if __name__ == '__main__':
    unittest.main()
