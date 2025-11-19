# Plugin Development Guide

This guide explains how to create plugins for ChatrixCD to extend its functionality.

## Overview

ChatrixCD has a powerful plugin system that allows you to:
- Add new features and functionality
- Integrate with external services
- Create alternative task monitoring mechanisms
- Customize bot behavior

## Plugin Structure

Every plugin must have the following structure:

```
plugins/
  your_plugin/
    meta.json       # Plugin metadata
    plugin.py       # Plugin implementation
    readme.md       # Plugin documentation
```

### Required Files

#### meta.json

Contains plugin metadata and configuration:

```json
{
  "name": "your_plugin_name",
  "description": "Brief description of what your plugin does",
  "version": "1.0.0",
  "author": "Your Name or Organization",
  "type": "generic",
  "category": "your_category",
  "enabled": true,
  "dependencies": [],
  "python_dependencies": [
    "package>=version"
  ]
}
```

**Fields:**
- `name` (required): Unique identifier for your plugin (lowercase, underscores allowed)
- `description` (required): What your plugin does
- `version` (required): Semantic version number (MAJOR.MINOR.PATCH)
- `author` (required): Your name or organization
- `type` (required): Plugin type - `"generic"`, `"task_monitor"`, etc.
- `category` (optional): Category for organization (default: `"general"`)
- `enabled` (optional): Whether plugin loads by default (default: `true`)
- `dependencies` (optional): List of other plugins this depends on
- `python_dependencies` (optional): List of Python packages from PyPI

#### plugin.py

Contains your plugin implementation. Must define a class that inherits from `Plugin` or a specialized base class:

```python
from chatrixcd.plugin_manager import Plugin

class YourPlugin(Plugin):
    async def initialize(self) -> bool:
        """Setup plugin. Return True if successful."""
        self.logger.info("Initializing YourPlugin")
        # Your initialization code here
        return True
    
    async def start(self) -> bool:
        """Start plugin. Return True if successful."""
        self.logger.info("Starting YourPlugin")
        # Your startup code here
        return True
    
    async def stop(self):
        """Stop plugin cleanly."""
        self.logger.info("Stopping YourPlugin")
        # Your shutdown code here
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up YourPlugin")
        # Your cleanup code here
```

#### readme.md

Documents your plugin usage, configuration, and features. Should include:
- Description
- Configuration options
- Usage examples
- Requirements/dependencies
- Troubleshooting

## Plugin Types

### Generic Plugin

Base plugin type for general extensions:

```python
from chatrixcd.plugin_manager import Plugin

class MyPlugin(Plugin):
    # Implement required methods
    pass
```

**Use for:**
- Custom commands
- External service integrations
- Background tasks
- Event handlers

### Task Monitor Plugin

For alternative task monitoring mechanisms:

```python
from chatrixcd.plugin_manager import TaskMonitorPlugin

class MyTaskMonitor(TaskMonitorPlugin):
    async def monitor_task(self, project_id, task_id, room_id, task_name):
        """Monitor a Semaphore task.
        
        Args:
            project_id: Semaphore project ID
            task_id: Task ID to monitor
            room_id: Matrix room for notifications
            task_name: Optional task name
        """
        # Your monitoring implementation
        pass
```

**Important:** Only one TaskMonitorPlugin can be active at a time. They are mutually exclusive.

**Use for:**
- Alternative monitoring methods (polling, webhooks, SSE)
- External notification systems
- Custom notification logic

## Plugin API

### Available Attributes

Every plugin has access to:

```python
self.bot          # ChatrixBot instance
self.config       # Plugin-specific configuration dict
self.metadata     # PluginMetadata instance
self.logger       # Logger instance for your plugin
```

### Bot API

Access bot functionality through `self.bot`:

```python
# Send messages
await self.bot.send_message(room_id, "Plain text", "<b>HTML</b>")

# Send reactions
await self.bot.send_reaction(room_id, event_id, "👍")

# Access Semaphore client
projects = await self.bot.semaphore.get_projects()
task = await self.bot.semaphore.get_task_status(project_id, task_id)

# Access Matrix client
rooms = self.bot.client.rooms
user_id = self.bot.client.user_id

# Access configuration
bot_config = self.bot.config
```

### Configuration

Plugin configuration is in `config.json`:

```json
{
  "plugins": {
    "your_plugin": {
      "enabled": true,
      "setting1": "value1",
      "setting2": 42
    }
  }
}
```

Access in your plugin:

```python
self.config.get('setting1', 'default_value')
self.config.get('setting2', 0)
```

### Logging

Use `self.logger` for logging:

```python
self.logger.info("Plugin started")
self.logger.debug("Debug information")
self.logger.warning("Warning message")
self.logger.error("Error occurred", exc_info=True)
```

### Status Information

Provide status information:

```python
def get_status(self):
    """Return plugin status."""
    status = super().get_status()
    
    # Add custom status fields
    status['custom_field'] = self.some_value
    status['is_active'] = self.is_active
    
    return status
```

Status appears in `!cd info` output.

## Lifecycle Methods

### initialize()

Called when plugin is loaded. Perform setup:
- Validate configuration
- Initialize resources
- Check dependencies
- Connect to services

Return `True` if successful, `False` to abort loading.

### start()

Called to start plugin functionality:
- Start background tasks
- Open connections
- Begin monitoring
- Register handlers

Return `True` if successful, `False` if failed.

### stop()

Called to stop plugin cleanly:
- Cancel background tasks
- Close connections
- Stop monitoring
- Unregister handlers

### cleanup()

Called when plugin is unloaded:
- Free resources
- Close file handles
- Delete temporary files
- Final cleanup

## Background Tasks

Run background tasks in your plugin:

```python
class MyPlugin(Plugin):
    def __init__(self, bot, config, metadata):
        super().__init__(bot, config, metadata)
        self.task = None
        self.running = False
    
    async def start(self):
        self.running = True
        self.task = asyncio.create_task(self._background_loop())
        return True
    
    async def stop(self):
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _background_loop(self):
        """Background task that runs periodically."""
        try:
            while self.running:
                await asyncio.sleep(60)
                # Do periodic work
                self.logger.debug("Background task tick")
        except asyncio.CancelledError:
            self.logger.info("Background task cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Background task error: {e}", exc_info=True)
```

## Error Handling

Always handle errors gracefully:

```python
async def some_method(self):
    try:
        # Your code
        result = await some_async_operation()
        return result
    except SpecificError as e:
        self.logger.error(f"Specific error: {e}")
        return None
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}", exc_info=True)
        return None
```

## Testing Your Plugin

1. Create your plugin directory in `plugins/`
2. Add `meta.json`, `plugin.py`, and `readme.md`
3. Enable it in `config.json`:
   ```json
   {
     "plugins": {
       "your_plugin": {
         "enabled": true
       }
     }
   }
   ```
4. Start ChatrixCD
5. Check logs for plugin loading messages
6. Verify with `!cd info` command

## Best Practices

### Code Quality
- Follow PEP 8 style guide
- Use type hints for function parameters
- Add docstrings to all public methods
- Keep methods focused and single-purpose

### Error Handling
- Use try/except for expected errors
- Log errors with appropriate severity
- Provide user-friendly error messages
- Never expose sensitive information in errors

### Configuration
- Validate configuration in `initialize()`
- Provide sensible defaults
- Document all configuration options
- Use type-appropriate defaults (int, str, bool, etc.)

### Logging
- Use appropriate log levels (debug, info, warning, error)
- Include context in log messages
- Don't log sensitive information
- Use `exc_info=True` for exceptions

### Resources
- Clean up in `cleanup()` method
- Cancel background tasks in `stop()`
- Close connections properly
- Handle cancellation gracefully

### Documentation
- Write clear readme.md with examples
- Document all configuration options
- Include troubleshooting section
- Provide usage examples

## Example: Simple Plugin

Complete example plugin:

```python
"""Example greeting plugin."""

import asyncio
from chatrixcd.plugin_manager import Plugin

class GreetingPlugin(Plugin):
    """Send periodic greeting messages."""
    
    def __init__(self, bot, config, metadata):
        super().__init__(bot, config, metadata)
        self.interval = config.get('interval', 3600)
        self.rooms = config.get('rooms', [])
        self.task = None
        self.running = False
    
    async def initialize(self):
        """Validate configuration."""
        if not self.rooms:
            self.logger.warning("No rooms configured for greetings")
        
        self.logger.info(f"Greeting interval: {self.interval}s")
        return True
    
    async def start(self):
        """Start greeting task."""
        self.running = True
        self.task = asyncio.create_task(self._greeting_loop())
        self.logger.info("Greeting plugin started")
        return True
    
    async def stop(self):
        """Stop greeting task."""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Greeting plugin stopped")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.stop()
    
    async def _greeting_loop(self):
        """Send periodic greetings."""
        try:
            while self.running:
                await asyncio.sleep(self.interval)
                await self._send_greetings()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Greeting loop error: {e}", exc_info=True)
    
    async def _send_greetings(self):
        """Send greeting to configured rooms."""
        for room_id in self.rooms:
            try:
                message = "👋 Hello from the greeting plugin!"
                await self.bot.send_message(room_id, message)
                self.logger.debug(f"Sent greeting to {room_id}")
            except Exception as e:
                self.logger.error(f"Failed to send greeting to {room_id}: {e}")
    
    def get_status(self):
        """Get plugin status."""
        status = super().get_status()
        status['interval'] = self.interval
        status['rooms_count'] = len(self.rooms)
        status['running'] = self.running
        return status
```

Configuration (`config.json`):

```json
{
  "plugins": {
    "greeting_plugin": {
      "enabled": true,
      "interval": 3600,
      "rooms": [
        "!room1:example.com",
        "!room2:example.com"
      ]
    }
  }
}
```

## Advanced Topics

### Dependencies

Specify Python package dependencies in `meta.json`:

```json
{
  "python_dependencies": [
    "aiohttp>=3.9.0",
    "requests>=2.28.0"
  ]
}
```

**Note:** Users must install dependencies manually. Document installation instructions in your readme.md.

### Plugin Dependencies

Depend on other plugins:

```json
{
  "dependencies": ["other_plugin_name"]
}
```

**Note:** Dependency resolution is not automatic. Document requirements in your readme.md.

### Accessing Other Plugins

Get other loaded plugins:

```python
# Check if plugin manager is available
if hasattr(self.bot, 'plugin_manager'):
    other_plugin = self.bot.plugin_manager.get_plugin('other_plugin')
    if other_plugin:
        # Use the other plugin
        pass
```

## Troubleshooting

### Plugin Not Loading

Check:
1. `meta.json` is valid JSON
2. `plugin.py` exists and has a Plugin subclass
3. `enabled` is `true` in both `meta.json` and `config.json`
4. No conflicting plugins (for task monitors)
5. Check bot logs for error messages

### Plugin Crashes on Start

Check:
1. Configuration is valid
2. Required dependencies are installed
3. External services are accessible
4. Logs for specific error messages

### Background Tasks Not Running

Check:
1. Task is created in `start()` method
2. Task is not being cancelled immediately
3. Exceptions are being caught and logged
4. `running` flag is set correctly

## Support

- Documentation: https://github.com/CJFWeatherhead/ChatrixCD
- Issues: https://github.com/CJFWeatherhead/ChatrixCD/issues
- Example: See `plugins/example_plugin/` for a complete working example

## License

Plugins must be compatible with ChatrixCD's license. See LICENSE file for details.
