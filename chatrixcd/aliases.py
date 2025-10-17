"""Alias management for ChatrixCD bot commands."""

import json
import logging
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class AliasManager:
    """Manage command aliases for the bot."""

    def __init__(self, aliases_file: str = "aliases.json"):
        """Initialize alias manager.
        
        Args:
            aliases_file: Path to aliases configuration file
        """
        self.aliases_file = aliases_file
        self.aliases: Dict[str, str] = {}
        self.load_aliases()

    def load_aliases(self):
        """Load aliases from file."""
        if not os.path.exists(self.aliases_file):
            logger.info(f"No aliases file found at {self.aliases_file}, starting with empty aliases")
            self.aliases = {}
            return

        try:
            with open(self.aliases_file, 'r') as f:
                self.aliases = json.load(f)
            logger.info(f"Loaded {len(self.aliases)} aliases from {self.aliases_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse aliases file: {e}")
            self.aliases = {}
        except Exception as e:
            logger.error(f"Failed to load aliases: {e}")
            self.aliases = {}

    def save_aliases(self) -> bool:
        """Save aliases to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.aliases_file, 'w') as f:
                json.dump(self.aliases, f, indent=2)
            logger.info(f"Saved {len(self.aliases)} aliases to {self.aliases_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save aliases: {e}")
            return False

    def add_alias(self, alias: str, command: str) -> bool:
        """Add or update an alias.
        
        Args:
            alias: The alias name
            command: The command to alias to
            
        Returns:
            True if added successfully, False otherwise
        """
        # Validate that alias doesn't conflict with existing commands
        reserved_commands = ['help', 'projects', 'templates', 'run', 'status', 'stop', 'logs', 'ping', 'info']
        if alias.lower() in reserved_commands:
            logger.warning(f"Cannot create alias '{alias}': conflicts with built-in command")
            return False

        self.aliases[alias] = command
        return self.save_aliases()

    def remove_alias(self, alias: str) -> bool:
        """Remove an alias.
        
        Args:
            alias: The alias to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if alias in self.aliases:
            del self.aliases[alias]
            return self.save_aliases()
        return False

    def get_alias(self, alias: str) -> Optional[str]:
        """Get the command for an alias.
        
        Args:
            alias: The alias to look up
            
        Returns:
            The aliased command or None if not found
        """
        return self.aliases.get(alias)

    def list_aliases(self) -> Dict[str, str]:
        """Get all aliases.
        
        Returns:
            Dictionary of all aliases
        """
        return self.aliases.copy()

    def resolve_command(self, command: str) -> str:
        """Resolve a command, expanding aliases if present.
        
        Args:
            command: The command to resolve (without prefix)
            
        Returns:
            The resolved command
        """
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return command

        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Check if this is an alias
        aliased = self.get_alias(cmd)
        if aliased:
            # If the alias includes arguments and user also provided arguments, append them
            if args:
                return f"{aliased} {args}"
            return aliased

        return command

    @staticmethod
    def validate_command(command: str) -> bool:
        """Validate that a command is a valid bot command.
        
        Args:
            command: The command to validate (without prefix)
            
        Returns:
            True if valid, False otherwise
        """
        valid_commands = ['help', 'projects', 'templates', 'run', 'status', 'stop', 'logs', 'ping', 'info']
        parts = command.strip().split()
        if not parts:
            return False

        cmd = parts[0].lower()
        return cmd in valid_commands
