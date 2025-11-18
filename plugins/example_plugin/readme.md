# Example Plugin

This is an example plugin that demonstrates the ChatrixCD plugin API. Use this as a template for creating your own plugins.

## Description

The example plugin shows you how to:
- Implement the plugin interface
- Handle plugin lifecycle (initialize, start, stop, cleanup)
- Access the bot instance and configuration
- Send messages to Matrix rooms
- Log information
- Provide status information

## Plugin Structure

Every ChatrixCD plugin must include:

1. **`meta.json`** - Plugin metadata file
2. **`plugin.py`** - Plugin implementation
3. **`readme.md`** - Plugin documentation (this file)

### meta.json Structure

```json
{
  "name": "your_plugin_name",
  "description": "Brief description of your plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "type": "generic",
  "category": "your_category",
  "enabled": false,
  "dependencies": [],
  "python_dependencies": []
}
```

**Fields:**
- `name`: Unique plugin identifier (lowercase, underscores allowed)
- `description`: What your plugin does
- `version`: Semantic version (major.minor.patch)
- `author`: Your name or organization
- `type`: Plugin type (`"generic"`, `"task_monitor"`, etc.)
- `category`: Plugin category for organization
- `enabled`: Whether plugin should be loaded by default
- `dependencies`: List of other plugins this depends on
- `python_dependencies`: List of Python packages required (from PyPI)

### plugin.py Implementation

Your `plugin.py` must define a class that inherits from `Plugin` or a specialized base class like `TaskMonitorPlugin`.

```python
from chatrixcd.plugin_manager import Plugin

class YourPlugin(Plugin):
    async def initialize(self) -> bool:
        # Setup code here
        return True
    
    async def start(self) -> bool:
        # Start your plugin's functionality
        return True
    
    async def stop(self):
        # Stop your plugin cleanly
        pass
    
    async def cleanup(self):
        # Clean up resources
        pass
```

## Configuration

Add plugin-specific configuration to your `config.json`:

```json
{
  "plugins": {
    "example_plugin": {
      "enabled": true,
      "example_setting": "value",
      "another_setting": 42
    }
  }
}
```

Access configuration in your plugin:

```python
self.config.get('example_setting', 'default_value')
```

## Accessing Bot Functionality

The plugin has access to the bot instance via `self.bot`:

```python
# Send a message to a room
await self.bot.send_message(room_id, "Plain text", "<b>HTML text</b>")

# Access Semaphore client
projects = await self.bot.semaphore.get_projects()

# Access configuration
bot_config = self.bot.config

# Send a reaction
await self.bot.send_reaction(room_id, event_id, "👍")
```

## Logging

Use `self.logger` to log messages:

```python
self.logger.info("Plugin started successfully")
self.logger.debug("Detailed debug information")
self.logger.warning("Warning message")
self.logger.error("Error occurred", exc_info=True)
```

## Plugin Types

### Generic Plugin

Base plugin type for general extensions:

```python
from chatrixcd.plugin_manager import Plugin

class MyPlugin(Plugin):
    # Implement required methods
    pass
```

### Task Monitor Plugin

For implementing alternative task monitoring mechanisms:

```python
from chatrixcd.plugin_manager import TaskMonitorPlugin

class MyMonitor(TaskMonitorPlugin):
    async def monitor_task(self, project_id, task_id, room_id, task_name):
        # Monitor task and send notifications
        pass
```

**Note:** Only one TaskMonitorPlugin can be active at a time.

## Testing Your Plugin

1. Create your plugin directory in `plugins/`
2. Add `meta.json` and `plugin.py`
3. Enable it in `config.json`
4. Restart ChatrixCD
5. Check logs for loading messages

## Best Practices

1. **Error Handling**: Always wrap async operations in try/except
2. **Resource Cleanup**: Clean up in `cleanup()` method
3. **Configuration Validation**: Check required config in `initialize()`
4. **Logging**: Use appropriate log levels
5. **Status Information**: Provide useful status in `get_status()`
6. **Dependencies**: List all Python package dependencies
7. **Documentation**: Write clear readme.md with examples

## Advanced Features

### Background Tasks

Run background tasks in your plugin:

```python
async def start(self) -> bool:
    self.background_task = asyncio.create_task(self._background_loop())
    return True

async def _background_loop(self):
    while self.monitoring_active:
        await asyncio.sleep(10)
        # Do periodic work
```

### Event Handlers

React to Matrix events:

```python
# You can register callbacks with the bot
# (requires bot support for plugin event handlers)
```

## Support

- Documentation: https://github.com/CJFWeatherhead/ChatrixCD
- Issues: https://github.com/CJFWeatherhead/ChatrixCD/issues
- Contributing: See CONTRIBUTING.md

## License

Same as ChatrixCD - see LICENSE file
