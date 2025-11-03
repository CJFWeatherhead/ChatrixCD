"""Tests for TUI menu dropdown fixes."""

import unittest
from unittest.mock import Mock, MagicMock


class TestMenuScreenColorFix(unittest.TestCase):
    """Test that MenuScreen colors are properly resolved."""
    
    def test_turbo_tui_css_variables_include_text(self):
        """Test that Turbo TUI CSS variables include proper text color."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        # Test each theme
        themes = ['default', 'midnight', 'grayscale', 'windows31', 'msdos']
        
        for theme in themes:
            with self.subTest(theme=theme):
                tui = ChatrixTurboTUI(mock_bot, mock_config, theme=theme)
                variables = tui.get_css_variables()
                
                # Check that 'text' variable exists
                self.assertIn('text', variables, f"Theme '{theme}' missing 'text' variable")
                
                # Check that 'text' is a proper color (hex code), not "auto 87%"
                text_value = variables['text']
                self.assertIsInstance(text_value, str)
                self.assertTrue(
                    text_value.startswith('#'),
                    f"Theme '{theme}' has invalid text value: {text_value}"
                )
                
                # Check that 'text-muted' variable exists
                self.assertIn('text-muted', variables, f"Theme '{theme}' missing 'text-muted' variable")
                text_muted_value = variables['text-muted']
                self.assertTrue(
                    text_muted_value.startswith('#'),
                    f"Theme '{theme}' has invalid text-muted value: {text_muted_value}"
                )
    
    def test_regular_tui_css_variables_include_text(self):
        """Test that regular TUI CSS variables include proper text color."""
        from chatrixcd.tui import ChatrixTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        # Test each theme
        themes = ['default', 'midnight', 'grayscale', 'windows31', 'msdos']
        
        for theme in themes:
            with self.subTest(theme=theme):
                tui = ChatrixTUI(mock_bot, mock_config, theme=theme)
                variables = tui.get_css_variables()
                
                # Check that 'text' variable exists
                self.assertIn('text', variables, f"Theme '{theme}' missing 'text' variable")
                
                # Check that 'text' is a proper color (hex code), not "auto 87%"
                text_value = variables['text']
                self.assertIsInstance(text_value, str)
                self.assertTrue(
                    text_value.startswith('#'),
                    f"Theme '{theme}' has invalid text value: {text_value}"
                )
    
    def test_theme_specific_text_colors(self):
        """Test that each theme has appropriate text colors."""
        from chatrixcd.tui_turbo import ChatrixTurboTUI
        
        mock_bot = Mock()
        mock_config = Mock()
        mock_config.get_bot_config.return_value = {}
        
        # Expected text colors for each theme
        expected_colors = {
            'default': '#FFFFFF',    # White for dark theme
            'midnight': '#00FFFF',   # Cyan for midnight theme
            'grayscale': '#FFFFFF',  # White for grayscale
            'windows31': '#000000',  # Black for light Windows 3.1 theme
            'msdos': '#FFAA00',     # Amber for MS-DOS theme
        }
        
        for theme, expected_color in expected_colors.items():
            with self.subTest(theme=theme):
                tui = ChatrixTurboTUI(mock_bot, mock_config, theme=theme)
                variables = tui.get_css_variables()
                
                self.assertEqual(
                    variables['text'], 
                    expected_color,
                    f"Theme '{theme}' has wrong text color"
                )


class TestMenuScreenKeyboardNavigation(unittest.TestCase):
    """Test that MenuScreen has proper keyboard navigation."""
    
    def test_menu_screen_has_arrow_key_bindings(self):
        """Test that MenuScreen includes arrow key bindings."""
        from chatrixcd.tui_turbo import MenuScreen
        
        # Check that the class has the expected bindings
        bindings = {binding.key for binding in MenuScreen.BINDINGS}
        
        self.assertIn('up', bindings, "MenuScreen missing 'up' binding")
        self.assertIn('down', bindings, "MenuScreen missing 'down' binding")
        self.assertIn('enter', bindings, "MenuScreen missing 'enter' binding")
        self.assertIn('escape', bindings, "MenuScreen missing 'escape' binding")
    
    def test_menu_screen_has_focus_action(self):
        """Test that MenuScreen has select_focused action method."""
        from chatrixcd.tui_turbo import MenuScreen
        
        menu_items = [("Test", "test_action")]
        menu = MenuScreen(menu_items)
        
        # Check that the action method exists
        self.assertTrue(
            hasattr(menu, 'action_select_focused'),
            "MenuScreen missing action_select_focused method"
        )
        self.assertTrue(
            callable(menu.action_select_focused),
            "action_select_focused is not callable"
        )
    
    def test_file_menu_screen_creation(self):
        """Test that FileMenuScreen can be created and has menu items."""
        from chatrixcd.tui_turbo import FileMenuScreen
        
        menu = FileMenuScreen()
        
        self.assertIsNotNone(menu.menu_items)
        self.assertGreater(len(menu.menu_items), 0, "FileMenuScreen has no menu items")
        
        # Verify it has expected menu items
        menu_labels = [label for label, _ in menu.menu_items if label != "---"]
        self.assertIn("Status", menu_labels)
        self.assertIn("Exit", menu_labels)
    
    def test_menu_screen_css_includes_focus_state(self):
        """Test that MenuScreen CSS includes focus state for keyboard navigation."""
        from chatrixcd.tui_turbo import MenuScreen
        
        css = MenuScreen.DEFAULT_CSS
        
        # Check that CSS includes focus pseudo-class
        self.assertIn(':focus', css, "MenuScreen CSS missing :focus state")
        
        # Check that it's defined for buttons
        self.assertIn('Button:focus', css, "MenuScreen CSS missing Button:focus")


if __name__ == '__main__':
    unittest.main()
