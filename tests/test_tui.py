"""Tests for TUI interface."""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import io


class TestTUIImport(unittest.TestCase):
    """Test TUI module can be imported and basic functionality."""

    def test_import_tui_module(self):
        """Test that TUI module can be imported."""
        try:
            from chatrixcd.tui import ChatrixTUI, run_tui
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import TUI module: {e}")
    
    def test_tui_screens_import(self):
        """Test that TUI screen classes can be imported."""
        try:
            from chatrixcd.tui import (
                AdminsScreen,
                RoomsScreen,
                SessionsScreen,
                SayScreen,
                LogScreen,
                SetScreen,
                ShowScreen,
                MessageScreen,
                BotStatusWidget
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import TUI screens: {e}")


class TestTUICreation(unittest.TestCase):
    """Test TUI object creation."""
    
    def test_create_tui_instance(self):
        """Test creating a TUI instance with mock bot and config."""
        from chatrixcd.tui import ChatrixTUI
        
        # Create mock bot and config
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {
            'admin_users': ['@admin:example.com'],
            'allowed_rooms': ['!room:example.com']
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
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        tui = ChatrixTUI(mock_bot, mock_config)
        
        self.assertEqual(tui.messages_processed, 0)
        self.assertEqual(tui.errors, 0)
        self.assertEqual(tui.warnings, 0)


class TestTUIScreens(unittest.TestCase):
    """Test TUI screen creation."""
    
    def test_admins_screen_creation(self):
        """Test creating an AdminsScreen."""
        from chatrixcd.tui import AdminsScreen
        
        admins = ['@admin1:example.com', '@admin2:example.com']
        screen = AdminsScreen(admins)
        
        self.assertIsNotNone(screen)
        self.assertEqual(screen.admins, admins)
    
    def test_rooms_screen_creation(self):
        """Test creating a RoomsScreen."""
        from chatrixcd.tui import RoomsScreen
        
        rooms = [
            {'id': '!room1:example.com', 'name': 'Room 1'},
            {'id': '!room2:example.com', 'name': 'Room 2'}
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
        self.assertEqual(widget.messages_processed, 0)
        self.assertEqual(widget.errors, 0)
        self.assertEqual(widget.warnings, 0)


class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration with TUI."""
    
    def test_log_only_flag(self):
        """Test -L/--log-only flag parsing."""
        import argparse
        from chatrixcd.main import parse_args
        
        with patch('sys.argv', ['chatrixcd', '-L']):
            args = parse_args()
            self.assertTrue(args.log_only)
        
        with patch('sys.argv', ['chatrixcd', '--log-only']):
            args = parse_args()
            self.assertTrue(args.log_only)
    
    def test_default_no_log_only(self):
        """Test that log_only defaults to False."""
        import argparse
        from chatrixcd.main import parse_args
        
        with patch('sys.argv', ['chatrixcd']):
            args = parse_args()
            self.assertFalse(args.log_only)


if __name__ == '__main__':
    unittest.main()
