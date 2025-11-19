# Migration Plan: Messages to Plugin

## Overview
Move the message management functionality from `chatrixcd/messages.py` into a dedicated plugin that loads by default. This enables customization of bot personality and responses through the plugin system.

## Current Implementation Analysis

### Files Involved
- `chatrixcd/messages.py` - MessageManager class (180 lines)
- `chatrixcd/commands.py` - Uses MessageManager for bot responses
- `messages.json.example` - Example message configuration

### Key Functionality
1. **Message Loading**: Load messages from `messages.json` with HJSON support
2. **Random Selection**: Get random messages from categories
3. **Template Formatting**: Format messages with parameters (e.g., {name}, {task_name})
4. **Default Messages**: Fallback to built-in messages if file missing
5. **File Watching**: Auto-reload on file changes
6. **Message Categories**: greetings, brush_off, cancel, timeout, task_start, ping_success, pet, scold

### Dependencies
- `hjson` for configuration parsing
- `FileWatcher` for auto-reload
- Used extensively in `CommandHandler` for personality

## Migration Steps

### Phase 1: Create Messages Plugin Structure

#### 1.1 Create Plugin Directory
```bash
mkdir -p plugins/messages
```

#### 1.2 Create meta.json
```json
{
  "name": "messages",
  "description": "Customizable bot personality and response messages. Provides the sassy, fun personality that makes ChatrixCD unique.",
  "version": "1.0.0",
  "author": "ChatrixCD Team",
  "type": "generic",
  "category": "core",
  "enabled": true,
  "dependencies": [],
  "python_dependencies": [
    "hjson>=3.1.0"
  ]
}
```

#### 1.3 Create plugin.json
```json
{
  "enabled": true,
  "messages_file": "messages.json",
  "auto_reload": true,
  "default_messages": {
    "greetings": [
      "{name} 👋",
      "Hi {name}! 👋",
      "Hello {name}! 😊"
    ],
    "brush_off": [
      "I can't talk to you 🫢 (Admin vibes only!)",
      "You're not my boss 🫠 ...unless you're an admin?"
    ],
    "cancel": [
      "Task execution cancelled. No problem! ❌",
      "Cancelled! Maybe another time. 👋"
    ],
    "timeout": [
      "I'll just go back to what I was doing then? 🙄",
      "Be more decisive next time, eh? 😏"
    ],
    "task_start": [
      "On it! Starting **{task_name}**... 🚀",
      "Here we go! Running **{task_name}**... 🏃"
    ],
    "ping_success": [
      "🏓 Semaphore server is alive and kicking! ✅",
      "🏓 Pong! Server is up! ✅"
    ],
    "pet": [
      "Aww, thanks! 🥰 *happy bot noises*",
      "You're the best! 😊 *purrs digitally*"
    ],
    "scold": [
      "Oh no! 😢 I'll try harder, I promise!",
      "Sorry... 😔 What did I do wrong?"
    ]
  }
}
```

### Phase 2: Refactor MessageManager into Plugin

#### 2.1 Create plugins/messages/plugin.py
```python
"""Messages Plugin - Bot personality and response messages."""

import hjson
import logging
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
from chatrixcd.plugin_manager import Plugin
from chatrixcd.file_watcher import FileWatcher

logger = logging.getLogger(__name__)


class MessagesPlugin(Plugin):
    """Plugin for managing bot response messages."""
    
    def __init__(self, bot: Any, config: Dict[str, Any], metadata: Any):
        super().__init__(bot, config, metadata)
        self.messages_file = config.get('messages_file', 'messages.json')
        self.auto_reload = config.get('auto_reload', True)
        self.default_messages = config.get('default_messages', {})
        self.messages: Dict[str, List[str]] = {}
        self._file_watcher: Optional[FileWatcher] = None
    
    async def initialize(self) -> bool:
        """Initialize the messages plugin."""
        self.logger.info(f"Initializing Messages plugin with file: {self.messages_file}")
        self.load_messages()
        
        if self.auto_reload:
            self._file_watcher = FileWatcher(
                file_path=self.messages_file,
                reload_callback=self.load_messages,
                auto_reload=True
            )
        
        return True
    
    async def start(self) -> bool:
        """Start the messages plugin."""
        self.logger.info("Messages plugin started")
        return True
    
    async def stop(self):
        """Stop the messages plugin."""
        if self._file_watcher:
            self._file_watcher.stop_auto_reload()
        self.logger.info("Messages plugin stopped")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.stop()
    
    def load_messages(self):
        """Load messages from file with HJSON support."""
        import os
        
        if not os.path.exists(self.messages_file):
            self.logger.info(f"Messages file {self.messages_file} not found, using defaults")
            self.messages = self.default_messages.copy()
            return
        
        try:
            # Check if file is empty
            if os.path.getsize(self.messages_file) == 0:
                self.logger.warning(f"Messages file {self.messages_file} is empty, using defaults")
                self.messages = self.default_messages.copy()
                return
            
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                content = f.read()
                loaded_messages = hjson.loads(content)
            
            # Merge loaded messages with defaults
            self.messages = self.default_messages.copy()
            self.messages.update(loaded_messages)
            
            self.logger.info(f"Loaded messages from {self.messages_file}")
        except Exception as e:
            self.logger.error(f"Failed to load messages: {e}, using defaults")
            self.messages = self.default_messages.copy()
    
    def get_random_message(self, category: str, **kwargs) -> str:
        """Get a random message from a category with formatting.
        
        Args:
            category: Message category (e.g., 'greetings', 'task_start')
            **kwargs: Template variables for formatting
            
        Returns:
            Formatted message string
        """
        messages = self.messages.get(category, [])
        if not messages:
            self.logger.warning(f"No messages found for category '{category}'")
            return f"[No message for {category}]"
        
        message_template = random.choice(messages)
        try:
            return message_template.format(**kwargs)
        except KeyError as e:
            self.logger.warning(f"Missing template variable {e} in message")
            return message_template
    
    def get_messages(self, category: str) -> List[str]:
        """Get all messages in a category."""
        return self.messages.get(category, []).copy()
    
    def add_message(self, category: str, message: str) -> bool:
        """Add a message to a category."""
        if category not in self.messages:
            self.messages[category] = []
        self.messages[category].append(message)
        return self.save_messages()
    
    def remove_message(self, category: str, index: int) -> bool:
        """Remove a message from a category by index."""
        if category not in self.messages:
            return False
        if index < 0 or index >= len(self.messages[category]):
            return False
        self.messages[category].pop(index)
        return self.save_messages()
    
    def save_messages(self) -> bool:
        """Save messages to file."""
        try:
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                hjson.dump(self.messages, f, indent=2)
            self.logger.info(f"Saved messages to {self.messages_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save messages: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status['categories'] = len(self.messages)
        status['total_messages'] = sum(len(msgs) for msgs in self.messages.values())
        status['messages_file'] = self.messages_file
        status['auto_reload'] = self.auto_reload
        return status
```

### Phase 3: Update CommandHandler Integration

#### 3.1 Modify commands.py
```python
# In CommandHandler.__init__
def __init__(self, bot, config, semaphore):
    # ... existing code ...
    
    # Remove: self.message_manager = MessageManager(...)
    # Messages are now managed by plugin
    
# Add method to get messages plugin
def _get_messages_plugin(self):
    """Get the messages plugin if loaded."""
    if hasattr(self.bot, 'plugin_manager'):
        return self.bot.plugin_manager.get_plugin('messages')
    return None

# Update all message usage
def _get_greeting(self, sender: str, room_id: str) -> str:
    """Get a random greeting message."""
    messages_plugin = self._get_messages_plugin()
    if messages_plugin:
        name = self._get_display_name(sender) if sender else "there"
        return messages_plugin.get_random_message('greetings', name=name)
    return "Hello!"  # Fallback

# Similar updates for:
# - _get_brush_off_message()
# - _get_cancel_message()
# - _get_timeout_message()
# - _get_task_start_message()
# - etc.
```

### Phase 4: Backwards Compatibility

#### 4.1 Legacy Support
- Keep `messages.json` in root directory
- Plugin reads from same location
- No changes to existing message files

#### 4.2 Graceful Degradation
```python
def _get_fallback_message(self, category: str) -> str:
    """Fallback messages when plugin not loaded."""
    fallbacks = {
        'greetings': "Hello! 👋",
        'brush_off': "Sorry, admin access only! 🔐",
        'cancel': "Task cancelled ❌",
        'timeout': "Request timed out ⏰",
        'task_start': "Starting task... 🚀",
        'ping_success': "🏓 Pong!",
        'pet': "Thanks! 🥰",
        'scold': "Sorry! 😢"
    }
    return fallbacks.get(category, "...")
```

### Phase 5: New Features via Plugin

#### 5.1 Message Management Commands
```python
async def handle_messages_command(self, room_id: str, args: List[str], sender: str):
    """Handle messages management command."""
    messages_plugin = self._get_messages_plugin()
    
    if not messages_plugin:
        await self.bot.send_message(
            room_id,
            "❌ Messages plugin is not loaded."
        )
        return
    
    if not args:
        # List message categories
        categories = list(messages_plugin.messages.keys())
        # ... format and send ...
    elif args[0] == 'list' and len(args) == 2:
        # List messages in category
        msgs = messages_plugin.get_messages(args[1])
        # ... format and send ...
    elif args[0] == 'add' and len(args) >= 3:
        # Add message to category
        result = messages_plugin.add_message(args[1], ' '.join(args[2:]))
        # ... send response ...
    # ... handle other subcommands ...
```

### Phase 6: Documentation

#### 6.1 Create plugins/messages/readme.md
```markdown
# Messages Plugin

Provides customizable bot personality through message templates.

## Configuration

### plugin.json
- `enabled`: Enable/disable plugin (default: true)
- `messages_file`: Path to messages file (default: messages.json)
- `auto_reload`: Auto-reload on file changes (default: true)
- `default_messages`: Fallback messages when file not found

## Message Categories

- `greetings`: User greetings
- `brush_off`: Non-admin responses
- `cancel`: Task cancellation
- `timeout`: Request timeouts
- `task_start`: Task initiation
- `ping_success`: Ping responses
- `pet`: Positive feedback
- `scold`: Negative feedback

## Template Variables

Messages support template variables:
- `{name}` - User display name
- `{task_name}` - Task name
- More as needed

## Customization

Create or edit `messages.json`:
```json
{
  "greetings": [
    "Hey {name}! 👋",
    "What's up {name}! 🌟"
  ],
  "task_start": [
    "Starting **{task_name}**... 🚀",
    "On it! Running **{task_name}**... 💪"
  ]
}
```

## Commands (Future)

- `!cd messages` - List categories
- `!cd messages list <category>` - List messages
- `!cd messages add <category> <message>` - Add message
- `!cd messages remove <category> <index>` - Remove message
```

#### 6.2 Update CHANGELOG.md
```markdown
### Changed
- **Messages**: Moved message management to plugin architecture
  - Bot personality now managed by `messages` plugin (enabled by default)
  - Backwards compatible with existing messages.json files
  - No configuration changes required
  - Enables runtime message customization
```

## Testing Requirements

### Unit Tests
```python
class TestMessagesPlugin(unittest.TestCase):
    def test_message_loading(self):
        """Test loading messages from file."""
        pass
    
    def test_random_message_selection(self):
        """Test random message retrieval."""
        pass
    
    def test_template_formatting(self):
        """Test message template variable substitution."""
        pass
    
    def test_fallback_to_defaults(self):
        """Test fallback when file missing."""
        pass
    
    def test_message_categories(self):
        """Test all message categories work."""
        pass
```

### Integration Tests
- Test messages in actual bot responses
- Test file auto-reload
- Test template variable substitution
- Test plugin disable scenario

## Rollout Strategy

### Phase 1: Development (1-2 days)
1. Create plugin structure
2. Migrate code from messages.py
3. Update CommandHandler integration
4. Implement graceful degradation
5. Write tests

### Phase 2: Testing (1 day)
1. Run unit tests
2. Test all message categories
3. Test template formatting
4. Test backwards compatibility
5. Test plugin disable scenario

### Phase 3: Documentation (0.5 days)
1. Plugin readme
2. Update main documentation
3. Update CHANGELOG
4. Document customization options

### Phase 4: Deployment
1. Merge to main branch
2. Include in next release
3. Announce personality customization feature

## Risk Assessment

### Low Risk
- Plugin enabled by default
- Uses same messages.json file
- Backwards compatible
- Fallback to simple messages if plugin disabled

### Medium Risk
- Bot personality is key feature
- Need to ensure all message points updated
- Template formatting must work correctly

### Mitigation
- Comprehensive test coverage of all message categories
- Fallback messages for graceful degradation
- Thorough manual testing of bot personality
- Easy rollback via plugin disable

## Success Criteria

✅ Messages plugin loads by default
✅ All message categories work correctly
✅ Template formatting works
✅ Bot personality unchanged from user perspective
✅ File auto-reload works
✅ Plugin can be disabled with fallback
✅ All tests pass
✅ Documentation complete

## Estimated Effort

- Development: 5-7 hours
- Testing: 3-4 hours
- Documentation: 1-2 hours
- **Total**: 9-13 hours (1.5-2 days)

## Future Enhancements

Once migrated to plugin:
1. **Runtime Message Management**: Commands to add/remove messages
2. **Message Templates**: More complex template system
3. **Conditional Messages**: Context-aware message selection
4. **Message Themes**: Presets for different personalities
5. **Message Statistics**: Track which messages are used most
6. **Custom Categories**: User-defined message categories
