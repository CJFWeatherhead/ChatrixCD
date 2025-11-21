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
