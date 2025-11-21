"""Plugin TUI integration system.

Provides base classes and utilities for plugins to integrate with the TUI.
"""

import logging
from typing import Optional, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from ..registry import ScreenRegistry
    from ..app import ChatrixTUI

logger = logging.getLogger(__name__)


class PluginTUIExtension:
    """Base class for plugin TUI extensions.
    
    Plugins can inherit from this class to provide TUI screens and widgets.
    """
    
    def __init__(self, plugin):
        """Initialize plugin TUI extension.
        
        Args:
            plugin: The plugin instance
        """
        self.plugin = plugin
        self.logger = logging.getLogger(f"tui.plugin.{plugin.metadata.name}")
        self._registered_screens = []
        
    @abstractmethod
    async def register_tui_screens(
        self,
        registry: 'ScreenRegistry',
        tui_app: 'ChatrixTUI'
    ):
        """Register TUI screens with the registry.
        
        Args:
            registry: Screen registry
            tui_app: TUI application instance
        """
        pass
        
    def _register_screen(
        self,
        registry: 'ScreenRegistry',
        name: str,
        screen_class,
        title: str,
        **kwargs
    ):
        """Helper to register a screen and track it.
        
        Args:
            registry: Screen registry
            name: Screen name
            screen_class: Screen class
            title: Screen title
            **kwargs: Additional registration parameters
        """
        success = registry.register(
            name=name,
            screen_class=screen_class,
            title=title,
            plugin_name=self.plugin.metadata.name,
            **kwargs
        )
        
        if success:
            self._registered_screens.append(name)
            self.logger.info(f"Registered screen: {name}")
        else:
            self.logger.warning(f"Failed to register screen: {name}")
            
    async def unregister_screens(self, registry: 'ScreenRegistry'):
        """Unregister all screens registered by this extension.
        
        Args:
            registry: Screen registry
        """
        for screen_name in self._registered_screens:
            registry.unregister(screen_name)
            self.logger.info(f"Unregistered screen: {screen_name}")
            
        self._registered_screens = []


class PluginScreenMixin:
    """Mixin for plugin screens to access plugin data.
    
    Add this to your BaseScreen subclass to get easy plugin access.
    """
    
    def get_plugin(self, plugin_name: str):
        """Get a plugin instance by name.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin instance or None
        """
        if not hasattr(self, 'tui_app'):
            return None
            
        if not hasattr(self.tui_app.bot, 'plugin_manager'):
            return None
            
        return self.tui_app.bot.plugin_manager.loaded_plugins.get(plugin_name)
        
    def get_plugin_config(self, plugin_name: str):
        """Get plugin configuration.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin config dict or None
        """
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.config
        return None
