# Migration Plan: Aliases to Plugin

## Overview
Move the alias functionality from `chatrixcd/aliases.py` into a dedicated plugin that loads by default. This will make alias management consistent with the plugin architecture while maintaining backwards compatibility.

## Current Implementation Analysis

### Files Involved
- `chatrixcd/aliases.py` - AliasManager class (130 lines)
- `chatrixcd/commands.py` - Uses AliasManager in CommandHandler
- `aliases.json.example` - Example configuration file

### Key Functionality
1. **Alias Loading**: Load aliases from `aliases.json` with auto-reload support
2. **Alias Resolution**: Resolve command aliases during command processing
3. **Alias Management**: Add/remove/list aliases via commands
4. **Reserved Commands**: Prevent aliasing of built-in commands
5. **File Watching**: Auto-reload on file changes

### Dependencies
- `FileWatcher` for auto-reload functionality
- Used by `CommandHandler` during command parsing

## Migration Steps

### Phase 1: Create Alias Plugin Structure

#### 1.1 Create Plugin Directory
```bash
mkdir -p plugins/aliases
```

#### 1.2 Create meta.json
```json
{
  "name": "aliases",
  "description": "Command alias management for ChatrixCD. Allows users to create shortcuts for frequently used commands.",
  "version": "1.0.0",
  "author": "ChatrixCD Team",
  "type": "generic",
  "category": "core",
  "enabled": true,
  "dependencies": [],
  "python_dependencies": []
}
```

#### 1.3 Create plugin.json
```json
{
  "enabled": true,
  "aliases_file": "aliases.json",
  "auto_reload": true,
  "reserved_commands": [
    "help", "projects", "templates", "run", "status",
    "stop", "logs", "ping", "info", "pet", "scold",
    "admins", "rooms", "exit", "aliases"
  ]
}
```

### Phase 2: Refactor AliasManager into Plugin

#### 2.1 Create plugins/aliases/plugin.py
```python
"""Aliases Plugin - Command alias management."""

import json
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
from chatrixcd.plugin_manager import Plugin
from chatrixcd.file_watcher import FileWatcher

logger = logging.getLogger(__name__)


class AliasesPlugin(Plugin):
    """Plugin for managing command aliases."""
    
    def __init__(self, bot: Any, config: Dict[str, Any], metadata: Any):
        super().__init__(bot, config, metadata)
        self.aliases_file = config.get('aliases_file', 'aliases.json')
        self.auto_reload = config.get('auto_reload', True)
        self.reserved_commands = config.get('reserved_commands', [])
        self.aliases: Dict[str, str] = {}
        self._file_watcher: Optional[FileWatcher] = None
    
    async def initialize(self) -> bool:
        """Initialize the aliases plugin."""
        self.logger.info(f"Initializing Aliases plugin with file: {self.aliases_file}")
        self.load_aliases()
        
        if self.auto_reload:
            self._file_watcher = FileWatcher(
                file_path=self.aliases_file,
                reload_callback=self.load_aliases,
                auto_reload=True
            )
        
        return True
    
    async def start(self) -> bool:
        """Start the aliases plugin."""
        self.logger.info("Aliases plugin started")
        return True
    
    async def stop(self):
        """Stop the aliases plugin."""
        if self._file_watcher:
            self._file_watcher.stop_auto_reload()
        self.logger.info("Aliases plugin stopped")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.stop()
    
    def load_aliases(self):
        """Load aliases from file."""
        # Implement loading logic (copy from AliasManager)
        pass
    
    def resolve_alias(self, command: str) -> str:
        """Resolve a command alias."""
        return self.aliases.get(command, command)
    
    def add_alias(self, alias: str, command: str) -> bool:
        """Add or update an alias."""
        # Implement (copy from AliasManager)
        pass
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an alias."""
        # Implement (copy from AliasManager)
        pass
    
    def list_aliases(self) -> Dict[str, str]:
        """Get all aliases."""
        return self.aliases.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status['aliases_count'] = len(self.aliases)
        status['aliases_file'] = self.aliases_file
        status['auto_reload'] = self.auto_reload
        return status
```

### Phase 3: Update CommandHandler Integration

#### 3.1 Modify commands.py
```python
# In CommandHandler.__init__
def __init__(self, bot, config, semaphore):
    # ... existing code ...
    
    # Remove: self.alias_manager = AliasManager(...)
    # Aliases are now managed by plugin
    
# Add method to get alias plugin
def _get_alias_plugin(self):
    """Get the aliases plugin if loaded."""
    if hasattr(self.bot, 'plugin_manager'):
        return self.bot.plugin_manager.get_plugin('aliases')
    return None

# In command parsing
def _resolve_alias(self, command: str) -> str:
    """Resolve command alias using plugin."""
    alias_plugin = self._get_alias_plugin()
    if alias_plugin:
        return alias_plugin.resolve_alias(command)
    return command
```

### Phase 4: Update Commands for Alias Management

#### 4.1 Update !cd aliases command
```python
async def handle_aliases_command(self, room_id: str, args: List[str], sender: str):
    """Handle aliases command - delegated to plugin."""
    alias_plugin = self._get_alias_plugin()
    
    if not alias_plugin:
        await self.bot.send_message(
            room_id,
            "❌ Aliases plugin is not loaded. Enable it in configuration."
        )
        return
    
    if not args:
        # List aliases
        aliases = alias_plugin.list_aliases()
        # ... format and send response ...
    elif args[0] == 'add' and len(args) >= 3:
        # Add alias
        result = alias_plugin.add_alias(args[1], ' '.join(args[2:]))
        # ... send response ...
    # ... handle other subcommands ...
```

### Phase 5: Backwards Compatibility

#### 5.1 Legacy Support
- Keep `aliases.json` in root directory (default location)
- Plugin reads from same location as before
- No changes needed to user's alias files

#### 5.2 Graceful Degradation
- Commands work without aliases plugin (no alias resolution)
- Clear error messages if plugin not loaded
- `!cd aliases` command informs user to enable plugin

### Phase 6: Documentation

#### 6.1 Create plugins/aliases/readme.md
```markdown
# Aliases Plugin

Provides command alias functionality for ChatrixCD.

## Configuration

### plugin.json
- `enabled`: Enable/disable plugin (default: true)
- `aliases_file`: Path to aliases file (default: aliases.json)
- `auto_reload`: Auto-reload on file changes (default: true)
- `reserved_commands`: Commands that cannot be aliased

## Usage

Automatically loaded by default. Use `!cd aliases` commands:
- `!cd aliases` - List all aliases
- `!cd aliases add <alias> <command>` - Add alias
- `!cd aliases remove <alias>` - Remove alias

## Migration

This plugin replaces the built-in alias functionality. No user action required.
```

#### 6.2 Update CHANGELOG.md
```markdown
### Changed
- **Aliases**: Moved alias management to plugin architecture
  - Aliases now managed by `aliases` plugin (enabled by default)
  - Backwards compatible with existing aliases.json files
  - No configuration changes required for existing users
```

## Testing Requirements

### Unit Tests
```python
class TestAliasesPlugin(unittest.TestCase):
    def test_alias_loading(self):
        """Test loading aliases from file."""
        pass
    
    def test_alias_resolution(self):
        """Test resolving command aliases."""
        pass
    
    def test_add_remove_alias(self):
        """Test adding and removing aliases."""
        pass
    
    def test_reserved_commands(self):
        """Test prevention of reserved command aliasing."""
        pass
```

### Integration Tests
- Test alias resolution in command processing
- Test !cd aliases commands
- Test file auto-reload
- Test plugin disable/enable

## Rollout Strategy

### Phase 1: Development (1-2 days)
1. Create plugin structure
2. Migrate code from aliases.py
3. Update CommandHandler integration
4. Write tests

### Phase 2: Testing (1 day)
1. Run unit tests
2. Manual testing with real aliases
3. Test backwards compatibility
4. Test plugin disable scenario

### Phase 3: Documentation (0.5 days)
1. Plugin readme
2. Update main documentation
3. Update CHANGELOG

### Phase 4: Deployment
1. Merge to main branch
2. Include in next release
3. Announce in release notes

## Risk Assessment

### Low Risk
- Plugin enabled by default (no user action)
- Uses same aliases.json file
- Backwards compatible

### Medium Risk
- Command resolution logic changes
- Need thorough testing of all command paths

### Mitigation
- Comprehensive test coverage
- Gradual rollout (dev → staging → production)
- Keep original aliases.py as reference during transition
- Easy rollback via plugin disable

## Success Criteria

✅ Aliases plugin loads by default
✅ All existing aliases work without changes
✅ !cd aliases commands function correctly
✅ File auto-reload works
✅ Plugin can be disabled without errors
✅ All tests pass
✅ Documentation complete

## Estimated Effort

- Development: 4-6 hours
- Testing: 2-3 hours
- Documentation: 1-2 hours
- **Total**: 7-11 hours (1-2 days)
