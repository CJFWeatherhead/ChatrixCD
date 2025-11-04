"""Tests for TUI menu navigation with arrow keys."""

import unittest
from unittest.mock import Mock


class TestTUIMenuNavigation(unittest.TestCase):
    """Test left/right arrow key navigation in TUI menus."""

    def test_turbo_tui_has_arrow_key_bindings(self):
        """Test that ChatrixTurboTUI has left/right arrow key bindings."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        # Check that the class has the expected bindings
        bindings = {binding.key for binding in ChatrixTurboTUI.BINDINGS}
        
        self.assertIn('left', bindings, "TUI missing 'left' arrow key binding")
        self.assertIn('right', bindings, "TUI missing 'right' arrow key binding")
    
    def test_turbo_tui_has_menu_navigation_methods(self):
        """Test that ChatrixTurboTUI has menu navigation action methods."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        tui = ChatrixTurboTUI(mock_bot, mock_config)
        
        # Check that navigation methods exist
        self.assertTrue(
            hasattr(tui, 'action_previous_menu'),
            "TUI missing action_previous_menu method"
        )
        self.assertTrue(
            hasattr(tui, 'action_next_menu'),
            "TUI missing action_next_menu method"
        )
        self.assertTrue(
            callable(tui.action_previous_menu),
            "action_previous_menu is not callable"
        )
        self.assertTrue(
            callable(tui.action_next_menu),
            "action_next_menu is not callable"
        )
    
    def test_turbo_tui_menu_order_tracking(self):
        """Test that ChatrixTurboTUI tracks current menu for navigation."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        tui = ChatrixTurboTUI(mock_bot, mock_config)
        
        # Check that menu tracking attributes exist
        self.assertTrue(
            hasattr(tui, 'menu_order'),
            "TUI missing menu_order attribute"
        )
        self.assertTrue(
            hasattr(tui, 'current_menu_index'),
            "TUI missing current_menu_index attribute"
        )
        
        # Check menu order
        self.assertEqual(
            tui.menu_order,
            ['file', 'edit', 'run', 'help'],
            "Menu order should be file, edit, run, help"
        )
        
        # Check initial index
        self.assertEqual(
            tui.current_menu_index,
            0,
            "Initial menu index should be 0 (file)"
        )
    
    def test_turbo_tui_menu_cycling(self):
        """Test that menu navigation cycles correctly."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        tui = ChatrixTurboTUI(mock_bot, mock_config)
        
        # Start at file (index 0)
        self.assertEqual(tui.current_menu_index, 0)
        
        # Mock push_screen to avoid actually showing screens
        tui.push_screen = Mock()
        
        # Navigate forward: file -> edit
        tui.action_next_menu()
        self.assertEqual(tui.current_menu_index, 1, "Should move to edit menu (index 1)")
        
        # Navigate forward: edit -> run
        tui.action_next_menu()
        self.assertEqual(tui.current_menu_index, 2, "Should move to run menu (index 2)")
        
        # Navigate forward: run -> help
        tui.action_next_menu()
        self.assertEqual(tui.current_menu_index, 3, "Should move to help menu (index 3)")
        
        # Navigate forward: help -> file (cycle back)
        tui.action_next_menu()
        self.assertEqual(tui.current_menu_index, 0, "Should cycle back to file menu (index 0)")
        
        # Navigate backward: file -> help (cycle back)
        tui.action_previous_menu()
        self.assertEqual(tui.current_menu_index, 3, "Should cycle back to help menu (index 3)")
        
        # Navigate backward: help -> run
        tui.action_previous_menu()
        self.assertEqual(tui.current_menu_index, 2, "Should move to run menu (index 2)")
    
    def test_turbo_tui_f_key_updates_menu_index(self):
        """Test that F-key menu shortcuts update the current menu index."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        tui = ChatrixTurboTUI(mock_bot, mock_config)
        
        # Mock push_screen to avoid actually showing screens
        tui.push_screen = Mock()
        
        # Test F1 -> File menu
        tui.action_show_file_menu()
        self.assertEqual(tui.current_menu_index, 0, "F1 should set index to 0 (file)")
        
        # Test F2 -> Edit menu
        tui.action_show_edit_menu()
        self.assertEqual(tui.current_menu_index, 1, "F2 should set index to 1 (edit)")
        
        # Test F3 -> Run menu
        tui.action_show_run_menu()
        self.assertEqual(tui.current_menu_index, 2, "F3 should set index to 2 (run)")
        
        # Test F4 -> Help menu
        tui.action_show_help_menu()
        self.assertEqual(tui.current_menu_index, 3, "F4 should set index to 3 (help)")
        
        # Now test that arrow keys work after F-key navigation
        tui.action_next_menu()
        self.assertEqual(tui.current_menu_index, 0, "Should cycle from help (3) to file (0)")


if __name__ == '__main__':
    unittest.main()
