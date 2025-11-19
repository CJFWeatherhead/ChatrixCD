# Implementation Plan: TUI Plugin Awareness

## Overview
Make the Text User Interface (TUI) plugin-aware, allowing users to view, manage, and control plugins through the interactive interface. This complements the existing `!cd info` command that shows plugin status.

## Current TUI Analysis

### TUI Framework
- Built with **Textual** framework
- Located in `chatrixcd/tui.py`
- Two modes: "turbo" (modern) and "classic" (original)
- Features: status monitoring, room management, device verification, configuration editing

### Existing Screens
1. **Main Status Screen**: Bot status, connections, metrics
2. **Room Management**: View/manage Matrix rooms
3. **Session Management**: Olm encryption sessions
4. **Device Verification**: E2E encryption verification
5. **Configuration**: Edit config interactively
6. **Logs**: Real-time log viewing
7. **Message Sending**: Send messages to rooms
8. **Alias Management**: Manage aliases

## Implementation Strategy

### Phase 1: Add Plugin Status Screen

#### 1.1 Create PluginStatusScreen Widget
```python
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button
from textual.containers import Container, Horizontal

class PluginStatusScreen(Container):
    """Screen showing plugin status and management."""
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Loaded Plugins", classes="section-title")
        yield DataTable(id="plugins-table")
        yield Horizontal(
            Button("Reload Plugins", id="reload-plugins", variant="primary"),
            Button("Plugin Info", id="plugin-info"),
            Button("Back", id="back-to-main", variant="default"),
            classes="button-row"
        )
    
    def on_mount(self) -> None:
        """Set up the data table."""
        table = self.query_one("#plugins-table", DataTable)
        table.add_columns("Name", "Version", "Type", "Status", "Active")
        self.refresh_plugin_list()
    
    def refresh_plugin_list(self) -> None:
        """Refresh the plugin list from bot."""
        table = self.query_one("#plugins-table", DataTable)
        table.clear()
        
        if not hasattr(self.app.bot, 'plugin_manager'):
            table.add_row("No plugin manager", "-", "-", "Disabled", "-")
            return
        
        plugins = self.app.bot.plugin_manager.get_all_plugins_status()
        for plugin in plugins:
            table.add_row(
                plugin['name'],
                plugin['version'],
                plugin['type'],
                "Enabled" if plugin['enabled'] else "Disabled",
                self._format_active_status(plugin)
            )
    
    def _format_active_status(self, plugin: dict) -> str:
        """Format plugin-specific status."""
        if plugin['type'] == 'task_monitor':
            return f"Tasks: {plugin.get('monitored_tasks', 0)}"
        return "Running"
```

#### 1.2 Add Menu Entry
```python
# In main TUI app
def compose(self) -> ComposeResult:
    # ... existing screens ...
    yield PluginStatusScreen(id="plugin-status")

# Add to menu/navigation
BINDINGS = [
    # ... existing bindings ...
    ("p", "show_plugins", "Plugins"),
]

def action_show_plugins(self) -> None:
    """Show plugin status screen."""
    self.query_one("#plugin-status").display = True
    self.query_one("#main-status").display = False
```

### Phase 2: Plugin Detail View

#### 2.1 PluginDetailModal
```python
from textual.screen import ModalScreen

class PluginDetailModal(ModalScreen):
    """Modal showing detailed plugin information."""
    
    def __init__(self, plugin_name: str):
        super().__init__()
        self.plugin_name = plugin_name
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"Plugin: {self.plugin_name}", classes="modal-title"),
            Static(id="plugin-details", classes="plugin-info"),
            Horizontal(
                Button("Enable/Disable", id="toggle-plugin"),
                Button("Restart", id="restart-plugin"),
                Button("Close", id="close-modal", variant="primary"),
                classes="modal-buttons"
            ),
            classes="plugin-modal"
        )
    
    def on_mount(self) -> None:
        """Load plugin details."""
        plugin = self.app.bot.plugin_manager.get_plugin(self.plugin_name)
        if plugin:
            details = self._format_plugin_details(plugin)
            self.query_one("#plugin-details").update(details)
    
    def _format_plugin_details(self, plugin) -> str:
        """Format detailed plugin information."""
        status = plugin.get_status()
        details = []
        details.append(f"Name: {status['name']}")
        details.append(f"Version: {status['version']}")
        details.append(f"Type: {status['type']}")
        details.append(f"Category: {status['category']}")
        details.append(f"Enabled: {status['enabled']}")
        
        # Add plugin-specific details
        if 'monitored_tasks' in status:
            details.append(f"Monitored Tasks: {status['monitored_tasks']}")
        if 'aliases_count' in status:
            details.append(f"Aliases: {status['aliases_count']}")
        if 'total_messages' in status:
            details.append(f"Messages: {status['total_messages']}")
        
        return "\n".join(details)
```

### Phase 3: Plugin Control Actions

#### 3.1 Enable/Disable Plugin
```python
async def action_toggle_plugin(self, plugin_name: str) -> None:
    """Toggle plugin enabled state."""
    plugin_manager = self.app.bot.plugin_manager
    plugin = plugin_manager.get_plugin(plugin_name)
    
    if not plugin:
        self.notify("Plugin not found", severity="error")
        return
    
    # This would require adding enable/disable methods to PluginManager
    if plugin.metadata.enabled:
        await plugin_manager.disable_plugin(plugin_name)
        self.notify(f"Disabled {plugin_name}", severity="information")
    else:
        await plugin_manager.enable_plugin(plugin_name)
        self.notify(f"Enabled {plugin_name}", severity="success")
    
    self.refresh_plugin_list()
```

#### 3.2 Reload Plugin
```python
async def action_reload_plugin(self, plugin_name: str) -> None:
    """Reload a specific plugin."""
    plugin_manager = self.app.bot.plugin_manager
    
    try:
        await plugin_manager.reload_plugin(plugin_name)
        self.notify(f"Reloaded {plugin_name}", severity="success")
        self.refresh_plugin_list()
    except Exception as e:
        self.notify(f"Failed to reload: {e}", severity="error")
```

#### 3.3 Reload All Plugins
```python
async def action_reload_all_plugins(self) -> None:
    """Reload all plugins."""
    plugin_manager = self.app.bot.plugin_manager
    
    self.notify("Reloading plugins...", severity="information")
    try:
        await plugin_manager.reload_all_plugins()
        self.notify("All plugins reloaded", severity="success")
        self.refresh_plugin_list()
    except Exception as e:
        self.notify(f"Failed to reload: {e}", severity="error")
```

### Phase 4: Plugin Manager Enhancements

#### 4.1 Add Plugin Control Methods
```python
# In PluginManager class

async def disable_plugin(self, plugin_name: str) -> bool:
    """Disable a loaded plugin without unloading."""
    if plugin_name not in self.loaded_plugins:
        return False
    
    plugin = self.loaded_plugins[plugin_name]
    await plugin.stop()
    plugin.metadata.enabled = False
    logger.info(f"Disabled plugin: {plugin_name}")
    return True

async def enable_plugin(self, plugin_name: str) -> bool:
    """Enable a disabled plugin."""
    if plugin_name not in self.loaded_plugins:
        # Try to load it
        return await self.load_plugin_by_name(plugin_name)
    
    plugin = self.loaded_plugins[plugin_name]
    if await plugin.start():
        plugin.metadata.enabled = True
        logger.info(f"Enabled plugin: {plugin_name}")
        return True
    return False

async def reload_plugin(self, plugin_name: str) -> bool:
    """Reload a specific plugin."""
    if plugin_name in self.loaded_plugins:
        await self.unload_plugin(plugin_name)
    
    plugin_dir = self.plugins_dir / plugin_name
    return await self.load_plugin(plugin_dir)

async def reload_all_plugins(self) -> int:
    """Reload all plugins."""
    # Store current enabled state
    enabled_plugins = [
        name for name, plugin in self.loaded_plugins.items()
        if plugin.metadata.enabled
    ]
    
    # Unload all
    await self.cleanup_plugins()
    
    # Reload
    count = await self.load_all_plugins()
    
    # Restore enabled state
    for name in enabled_plugins:
        if name in self.loaded_plugins:
            await self.enable_plugin(name)
    
    return count
```

### Phase 5: Real-time Plugin Updates

#### 5.1 Plugin Status Refresh
```python
# Add auto-refresh to plugin screen
class PluginStatusScreen(Container):
    def on_mount(self) -> None:
        # ... existing code ...
        self.set_interval(5.0, self.refresh_plugin_list)  # Refresh every 5s
    
    def refresh_plugin_list(self) -> None:
        """Refresh plugin list with current status."""
        # ... update table with latest status ...
```

#### 5.2 Plugin Event Notifications
```python
# In TUI app, listen for plugin events
def on_plugin_loaded(self, event: PluginLoadedEvent) -> None:
    """Handle plugin loaded event."""
    self.notify(f"Plugin loaded: {event.plugin_name}", severity="success")
    self.refresh_plugins()

def on_plugin_error(self, event: PluginErrorEvent) -> None:
    """Handle plugin error event."""
    self.notify(f"Plugin error: {event.message}", severity="error")
```

### Phase 6: Plugin Configuration UI

#### 6.1 Edit Plugin Config
```python
class PluginConfigModal(ModalScreen):
    """Modal for editing plugin configuration."""
    
    def __init__(self, plugin_name: str):
        super().__init__()
        self.plugin_name = plugin_name
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"Configure: {self.plugin_name}", classes="modal-title"),
            TextArea(id="plugin-config", language="json"),
            Horizontal(
                Button("Save", id="save-config", variant="primary"),
                Button("Cancel", id="cancel", variant="default"),
                classes="modal-buttons"
            ),
            classes="config-modal"
        )
    
    def on_mount(self) -> None:
        """Load plugin configuration."""
        config = self._load_plugin_config(self.plugin_name)
        text_area = self.query_one("#plugin-config", TextArea)
        text_area.text = json.dumps(config, indent=2)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-config":
            await self._save_plugin_config()
            self.dismiss(True)
        elif event.button.id == "cancel":
            self.dismiss(False)
```

### Phase 7: UI/UX Enhancements

#### 7.1 Plugin Status Colors
```css
/* In TUI stylesheet */
.plugin-enabled {
    color: $success;
}

.plugin-disabled {
    color: $error;
}

.plugin-warning {
    color: $warning;
}
```

#### 7.2 Plugin Icons/Indicators
```python
def _get_plugin_icon(self, plugin_type: str) -> str:
    """Get icon for plugin type."""
    icons = {
        'task_monitor': '📊',
        'generic': '🔌',
        'core': '⚙️',
    }
    return icons.get(plugin_type, '🔌')
```

### Phase 8: Help and Documentation

#### 8.1 Plugin Help Screen
```python
class PluginHelpScreen(Container):
    """Screen showing plugin system help."""
    
    def compose(self) -> ComposeResult:
        yield Static("Plugin System Help", classes="section-title")
        yield Static("""
        Plugins extend ChatrixCD functionality:
        
        - View: See loaded plugins and status
        - Enable/Disable: Control plugin activation
        - Reload: Restart plugins to apply changes
        - Configure: Edit plugin settings
        
        Key Bindings:
        - p: Show plugins screen
        - r: Reload all plugins
        - i: Show plugin info
        """, classes="help-text")
        yield Button("Back", id="back", variant="primary")
```

## Testing Requirements

### Unit Tests
```python
class TestTUIPlugins(unittest.TestCase):
    def test_plugin_status_display(self):
        """Test plugin status screen displays correctly."""
        pass
    
    def test_plugin_enable_disable(self):
        """Test enabling and disabling plugins."""
        pass
    
    def test_plugin_reload(self):
        """Test reloading plugins."""
        pass
```

### Integration Tests
- Test TUI plugin screen with real plugins
- Test plugin control actions
- Test config editing
- Test error handling

### Manual Testing Checklist
- [ ] Plugin status screen displays correctly
- [ ] Plugin details modal shows accurate info
- [ ] Enable/disable plugin works
- [ ] Reload plugin works
- [ ] Reload all plugins works
- [ ] Plugin config editing works
- [ ] Real-time status updates work
- [ ] Error messages display properly
- [ ] Navigation/key bindings work
- [ ] Both "turbo" and "classic" modes work

## Rollout Strategy

### Phase 1: Development (2-3 days)
1. Add PluginStatusScreen
2. Implement plugin control methods
3. Add plugin detail view
4. Add configuration UI
5. Write tests

### Phase 2: Testing (1 day)
1. Unit tests
2. Integration tests
3. Manual testing in both TUI modes
4. Test with different plugins

### Phase 3: Documentation (0.5 days)
1. Update TUI documentation
2. Add plugin management guide
3. Update CHANGELOG

### Phase 4: Deployment
1. Merge to main branch
2. Include in next release
3. Announce feature

## Risk Assessment

### Medium Risk
- TUI is interactive and complex
- Plugin control could affect running tasks
- Real-time updates need careful handling

### Mitigation
- Comprehensive testing
- Confirm dialogs for destructive actions
- Graceful error handling
- Ability to disable TUI plugin features via config

## Success Criteria

✅ Plugin status screen displays all plugins
✅ Plugin details show comprehensive information
✅ Enable/disable plugins works safely
✅ Reload plugins works without crashes
✅ Configuration editing works
✅ Real-time updates work smoothly
✅ Works in both "turbo" and "classic" modes
✅ Error handling is robust
✅ Documentation is complete

## Estimated Effort

- PluginStatusScreen: 4-6 hours
- Plugin control methods: 3-4 hours
- Detail view and modals: 3-4 hours
- Configuration UI: 3-4 hours
- Testing: 4-6 hours
- Documentation: 2-3 hours
- **Total**: 19-27 hours (2.5-3.5 days)

## Future Enhancements

1. **Plugin Marketplace**: Browse/install plugins from repository
2. **Plugin Dependencies**: Visual dependency graph
3. **Plugin Logs**: View plugin-specific logs
4. **Plugin Metrics**: Performance and usage metrics
5. **Plugin Updates**: Check and install updates
6. **Plugin Search**: Search/filter plugins
7. **Plugin Recommendations**: Suggest plugins based on usage
