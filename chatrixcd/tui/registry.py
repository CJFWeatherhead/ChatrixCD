"""Screen registry for managing available TUI screens.

Allows plugins to register their own screens dynamically.
"""

import logging
from typing import Dict, Type, Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScreenRegistration:
    """Registration information for a screen."""
    
    name: str
    screen_class: Type
    title: str
    key_binding: Optional[str] = None
    priority: int = 50  # Lower priority = appears first in menu
    category: str = "general"
    icon: str = "•"
    plugin_name: Optional[str] = None
    condition: Optional[Callable[[], bool]] = None  # Function to check if screen should be shown


class ScreenRegistry:
    """Registry for managing available TUI screens.
    
    This allows plugins and core modules to register their screens
    for display in the TUI menu system.
    """
    
    def __init__(self):
        """Initialize the screen registry."""
        self._screens: Dict[str, ScreenRegistration] = {}
        self._key_bindings: Dict[str, str] = {}
        
    def register(
        self,
        name: str,
        screen_class: Type,
        title: str,
        key_binding: Optional[str] = None,
        priority: int = 50,
        category: str = "general",
        icon: str = "•",
        plugin_name: Optional[str] = None,
        condition: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Register a screen.
        
        Args:
            name: Unique identifier for the screen
            screen_class: The screen class to instantiate
            title: Display title for the screen
            key_binding: Keyboard shortcut (e.g., 's' for status)
            priority: Display priority (lower = higher priority)
            category: Category for grouping screens
            icon: Icon/emoji for the screen
            plugin_name: Name of the plugin registering this screen
            condition: Optional function to check if screen should be shown
            
        Returns:
            True if registration successful, False if name already exists
        """
        if name in self._screens:
            logger.warning(f"Screen '{name}' already registered, skipping")
            return False
            
        if key_binding and key_binding in self._key_bindings:
            logger.warning(f"Key binding '{key_binding}' already in use, removing it")
            key_binding = None
            
        registration = ScreenRegistration(
            name=name,
            screen_class=screen_class,
            title=title,
            key_binding=key_binding,
            priority=priority,
            category=category,
            icon=icon,
            plugin_name=plugin_name,
            condition=condition,
        )
        
        self._screens[name] = registration
        if key_binding:
            self._key_bindings[key_binding] = name
            
        logger.info(f"Registered screen '{name}' (key: {key_binding}, plugin: {plugin_name})")
        return True
        
    def unregister(self, name: str) -> bool:
        """Unregister a screen.
        
        Args:
            name: Screen name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name not in self._screens:
            return False
            
        registration = self._screens[name]
        if registration.key_binding:
            self._key_bindings.pop(registration.key_binding, None)
            
        del self._screens[name]
        logger.info(f"Unregistered screen '{name}'")
        return True
        
    def get(self, name: str) -> Optional[ScreenRegistration]:
        """Get a screen registration by name.
        
        Args:
            name: Screen name
            
        Returns:
            ScreenRegistration if found, None otherwise
        """
        return self._screens.get(name)
        
    def get_by_key(self, key: str) -> Optional[ScreenRegistration]:
        """Get a screen registration by key binding.
        
        Args:
            key: Key binding
            
        Returns:
            ScreenRegistration if found, None otherwise
        """
        screen_name = self._key_bindings.get(key)
        if screen_name:
            return self._screens.get(screen_name)
        return None
        
    def get_all(self, category: Optional[str] = None) -> list[ScreenRegistration]:
        """Get all registered screens, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of ScreenRegistration objects, sorted by priority
        """
        screens = list(self._screens.values())
        
        if category:
            screens = [s for s in screens if s.category == category]
            
        # Filter by condition
        screens = [s for s in screens if not s.condition or s.condition()]
        
        # Sort by priority, then name
        screens.sort(key=lambda s: (s.priority, s.name))
        
        return screens
        
    def get_categories(self) -> list[str]:
        """Get list of all categories.
        
        Returns:
            List of unique category names
        """
        categories = {s.category for s in self._screens.values()}
        return sorted(categories)
        
    def clear_plugin_screens(self, plugin_name: str) -> int:
        """Remove all screens registered by a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Number of screens removed
        """
        to_remove = [
            name for name, reg in self._screens.items()
            if reg.plugin_name == plugin_name
        ]
        
        for name in to_remove:
            self.unregister(name)
            
        return len(to_remove)
