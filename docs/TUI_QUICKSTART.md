"""
# TUI Quick Start Guide

## For Users

### Running the TUI

Simply run:
```bash
chatrixcd
```

### Key Features

- **Plugin Screens**: Plugins can add their own menu items
- **Comprehensive Testing**: Full test coverage
- **Modular Architecture**: Clean code, easy to maintain
- **Event-Driven**: Responsive and efficient

## For Plugin Developers

### Adding a TUI Screen to Your Plugin

**Step 1: Create your screen class**

```python
# In your plugin file or separate module
from chatrixcd.tui.screens.base import BaseScreen
from chatrixcd.tui.widgets.common import DataGrid
from textual.containers import Container
from textual.widgets import Static

class MyPluginScreen(BaseScreen):
    \"\"\"Screen for my plugin.\"\"\"
    
    SCREEN_TITLE = "My Plugin"
    
    def compose_content(self):
        \"\"\"Compose screen content.\"\"\"
        with Container():
            yield Static("[bold]My Plugin Screen[/bold]")
            yield DataGrid(columns=["Column 1", "Column 2"])
    
    async def refresh_data(self):
        \"\"\"Refresh data from plugin.\"\"\"
        # Get plugin data
        plugin = self.get_plugin('my_plugin')
        if plugin:
            data = plugin.get_some_data()
            # Update UI
```

**Step 2: Implement TUI registration in your plugin**

```python
class MyPlugin(Plugin):
    # ... existing plugin code ...
    
    async def register_tui_screens(self, registry, tui_app):
        \"\"\"Register TUI screens for this plugin.
        
        This method is called when TUI initializes.
        
        Args:
            registry: ScreenRegistry instance
            tui_app: ChatrixTUI instance
        \"\"\"
        registry.register(
            name="my_plugin_screen",
            screen_class=MyPluginScreen,
            title="My Plugin",
            key_binding="p",  # Press 'p' to open
            priority=50,  # Lower = appears first
            category="plugins",
            icon="🔌",
            plugin_name=self.metadata.name,
        )
```

**Step 3: Use PluginScreenMixin for easy plugin access**

```python
from chatrixcd.tui.plugin_integration import PluginScreenMixin

class MyPluginScreen(BaseScreen, PluginScreenMixin):
    async def refresh_data(self):
        # Easy plugin access
        plugin = self.get_plugin('my_plugin')
        config = self.get_plugin_config('my_plugin')
```

### Using Plugin TUI Extension Helper

For cleaner organization, use `PluginTUIExtension`:

```python
from chatrixcd.tui.plugin_integration import PluginTUIExtension

class MyPluginTUI(PluginTUIExtension):
    \"\"\"TUI extension for my plugin.\"\"\"
    
    async def register_tui_screens(self, registry, tui_app):
        \"\"\"Register all plugin screens.\"\"\"
        self._register_screen(
            registry=registry,
            name="my_plugin_main",
            screen_class=MyPluginMainScreen,
            title="My Plugin",
            key_binding="p",
        )
        
        self._register_screen(
            registry=registry,
            name="my_plugin_settings",
            screen_class=MyPluginSettingsScreen,
            title="My Plugin Settings",
            category="settings",
        )

# In your plugin:
async def register_tui_screens(self, registry, tui_app):
    tui = MyPluginTUI(self)
    await tui.register_tui_screens(registry, tui_app)
```

## For Core Contributors

### Adding a New Core Screen

**1. Create screen file**

```bash
# Create new file
touch chatrixcd/tui/screens/my_screen.py
```

**2. Implement screen**

```python
from .base import BaseScreen
from textual.containers import Container
from textual.widgets import Static

class MyScreen(BaseScreen):
    SCREEN_TITLE = "My Screen"
    
    def compose_content(self):
        with Container():
            yield Static("My content")
    
    async def refresh_data(self):
        # Update data
        pass
```

**3. Register in app.py**

```python
# In _register_core_screens()
self.screen_registry.register(
    name="my_screen",
    screen_class=MyScreen,
    title="My Screen",
    key_binding="m",
    priority=35,
    category="core",
    icon="📄",
)
```

**4. Add tests**

```python
# In tests/test_tui_pilot.py
async def test_my_screen(self):
    app = ChatrixTUI(mock_bot, mock_config)
    
    async with app.run_test() as pilot:
        await pilot.press("m")
        self.assertIsInstance(app.screen, MyScreen)
```

### Creating Reusable Widgets

**1. Add to widgets/common.py**

```python
class MyWidget(BaseWidget):
    \"\"\"My reusable widget.\"\"\"
    
    value: reactive[str] = reactive("")
    
    def render(self) -> str:
        return f"Value: {self.value}"
```

**2. Use in screens**

```python
class MyScreen(BaseScreen):
    def compose_content(self):
        yield MyWidget(id="my-widget")
    
    async def refresh_data(self):
        widget = self.query_one("#my-widget", MyWidget)
        widget.value = "Updated"
```

## Testing Your TUI Code

### Unit Tests

Test individual components:

```python
import unittest
from chatrixcd.tui.registry import ScreenRegistry

class TestMyFeature(unittest.TestCase):
    def test_screen_registration(self):
        registry = ScreenRegistry()
        registry.register(
            name="test",
            screen_class=MyScreen,
            title="Test",
        )
        self.assertIsNotNone(registry.get("test"))
```

### Pilot Tests

Test interactive workflows:

```python
import unittest
from chatrixcd.tui.app import ChatrixTUI

class TestMyWorkflow(unittest.IsolatedAsyncioTestCase):
    async def test_navigation(self):
        app = ChatrixTUI(mock_bot, mock_config)
        
        async with app.run_test(size=(80, 30)) as pilot:
            # Navigate to screen
            await pilot.press("m")
            await pilot.pause()
            
            # Check screen
            self.assertIsInstance(app.screen, MyScreen)
            
            # Go back
            await pilot.press("escape")
```

### Running Tests

```bash
# Run all TUI tests
python -m unittest tests.test_tui_core
python -m unittest tests.test_tui_pilot

# Run specific test
python -m unittest tests.test_tui_core.TestScreenRegistry

# Verbose mode
python -m unittest discover -v -s tests -p "test_tui_*.py"
```

## Common Patterns

### Screen with Data Table

```python
class MyDataScreen(BaseScreen):
    def compose_content(self):
        yield DataGrid(columns=["Name", "Value"], id="data-table")
    
    async def refresh_data(self):
        table = self.query_one("#data-table", DataGrid)
        table.clear()
        
        for item in self.get_data():
            table.add_row(item['name'], item['value'])
```

### Screen with Form Input

```python
from chatrixcd.tui.widgets.common import FormField

class MyFormScreen(BaseScreen):
    def compose_content(self):
        yield FormField(
            label="Username",
            field_type="text",
            id="username"
        )
        yield Button("Submit", id="submit")
    
    async def on_button_pressed(self, event):
        if event.button.id == "submit":
            field = self.query_one("#username", FormField)
            value = field.get_value()
            # Process value
```

### Modal Dialog

```python
from textual.screen import ModalScreen

class MyModal(ModalScreen):
    def compose(self):
        with Container(classes="modal"):
            yield Static("Are you sure?")
            yield Button("Yes", id="yes")
            yield Button("No", id="no")
    
    async def on_button_pressed(self, event):
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

# Use in screen:
result = await self.app.push_screen(MyModal())
if result:
    # User confirmed
    pass
```

## Troubleshooting

### TUI Not Loading

Check environment variable:
```bash
echo $DEPRECATED
# Should be "2"
```

Check logs:
```bash
chatrixcd -vv | grep "TUI"
# Should see "Using TUI (modular)"
```

### Plugin Screen Not Appearing

1. Check plugin is loaded: `!cd info`
2. Check `register_tui_screens()` is implemented
3. Check for errors in logs
4. Verify screen name is unique
5. Check condition callback (if used)

### Tests Failing

1. Ensure all dependencies installed
2. Check mock objects are properly configured
3. Use `await pilot.pause()` between actions
4. Check screen sizes in tests (default: 80x30)

## Resources

- [Full Architecture Doc](TUI_V2_ARCHITECTURE.md)
- [Textual Documentation](https://textual.textualize.io/)
- [Example Plugin](../plugins/example_plugin/)
- [Test Examples](../tests/test_tui_pilot.py)

## Getting Help

- Read the architecture documentation
- Check test examples for patterns
- Ask in Matrix: #chatrixcd:matrix.org
- Open GitHub issue with [TUI] prefix
"""
