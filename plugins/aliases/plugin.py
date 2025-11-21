"""Aliases Plugin - Command alias management."""

import json
import logging
import os
from typing import Dict, Optional, List, Any
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
        if not os.path.exists(self.aliases_file):
            self.logger.info(f"No aliases file found at {self.aliases_file}, starting with empty aliases")
            self.aliases = {}
            return

        try:
            # Check if file is empty
            if os.path.getsize(self.aliases_file) == 0:
                self.logger.info(f"Aliases file {self.aliases_file} is empty, starting with empty aliases")
                self.aliases = {}
                return
                
            with open(self.aliases_file, 'r', encoding='utf-8') as f:
                self.aliases = json.load(f)
            self.logger.info(f"Loaded {len(self.aliases)} aliases from {self.aliases_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse aliases file: {e}")
            self.aliases = {}
        except Exception as e:
            self.logger.error(f"Failed to load aliases: {e}")
            self.aliases = {}

    def save_aliases(self) -> bool:
        """Save aliases to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.aliases_file, 'w', encoding='utf-8') as f:
                json.dump(self.aliases, f, indent=2)
            self.logger.info(f"Saved {len(self.aliases)} aliases to {self.aliases_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save aliases: {e}")
            return False

    def resolve_alias(self, command: str) -> str:
        """Resolve a command alias."""
        return self.aliases.get(command, command)
    
    def add_alias(self, alias: str, command: str) -> bool:
        """Add or update an alias."""
        if alias.lower() in self.reserved_commands:
            self.logger.warning(f"Cannot create alias '{alias}': conflicts with built-in command")
            return False

        self.aliases[alias] = command
        return self.save_aliases()
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an alias."""
        if alias not in self.aliases:
            return False
        del self.aliases[alias]
        return self.save_aliases()
    
    def list_aliases(self) -> Dict[str, str]:
        """Get all aliases."""
        return self.aliases.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        # Plugin base class doesn't have get_status, so we create a dict directly
        status = {
            'name': self.metadata.name,
            'version': self.metadata.version,
            'enabled': self.metadata.enabled,
            'aliases_count': len(self.aliases),
            'aliases_file': self.aliases_file,
            'auto_reload': self.auto_reload
        }
        return status
    
    def validate_command(self, command: str) -> bool:
        """Validate that a command is a valid bot command."""
        parts = command.strip().split()
        if not parts:
            return False
        return parts[0].lower() in self.reserved_commands
    
    async def register_tui_screens(self, registry, tui_app):
        """Register TUI screens for this plugin.
        
        This method is called by the TUI to allow plugins to
        register their own screens and interfaces.
        
        Args:
            registry: ScreenRegistry instance
            tui_app: ChatrixTUI instance
        """
        try:
            from chatrixcd.tui.plugins.aliases_tui import AliasesPluginTUI
            
            tui_extension = AliasesPluginTUI(self)
            await tui_extension.register_tui_screens(registry, tui_app)
            
            self.logger.info("Registered TUI screens for aliases plugin")
        except ImportError:
            self.logger.debug("TUI not available, skipping screen registration")
