"""Plugin management system for ChatrixCD.

This module provides a plugin system that allows extending ChatrixCD functionality
through loadable modules. Plugins can provide task monitoring backends (polling,
webhooks), custom commands, or other extensions.
"""

import importlib.util
import json
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginMetadata:
    """Metadata for a plugin loaded from meta.json."""

    def __init__(self, data: Dict[str, Any], plugin_dir: Path):
        """Initialize plugin metadata.

        Args:
            data: Metadata dictionary from meta.json
            plugin_dir: Path to the plugin directory
        """
        self.name = data.get("name", "Unknown")
        self.description = data.get("description", "")
        self.version = data.get("version", "0.0.0")
        self.author = data.get("author", "Unknown")
        self.dependencies = data.get("dependencies", [])
        self.python_dependencies = data.get("python_dependencies", [])
        self.plugin_type = data.get("type", "generic")
        self.category = data.get("category", "general")
        self.plugin_dir = plugin_dir
        self.enabled = data.get("enabled", True)

    def __repr__(self):
        return f"PluginMetadata(name={self.name}, version={self.version}, type={self.plugin_type})"


class Plugin(ABC):
    """Base class for all ChatrixCD plugins.

    Plugins should inherit from this class and implement the required methods.
    """

    def __init__(self, bot: Any, config: Dict[str, Any], metadata: PluginMetadata):
        """Initialize the plugin.

        Args:
            bot: Reference to the ChatrixBot instance
            config: Plugin-specific configuration
            metadata: Plugin metadata
        """
        self.bot = bot
        self.config = config
        self.metadata = metadata
        self.logger = logging.getLogger(f"plugin.{metadata.name}")
        # Track runtime enabled state (True if plugin is loaded and initialized)
        self._enabled = True

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin.

        Called when the plugin is loaded. Should perform any necessary setup.

        Returns:
            True if initialization was successful, False otherwise
        """

    @abstractmethod
    async def start(self) -> bool:
        """Start the plugin.

        Called to start the plugin's main functionality.

        Returns:
            True if started successfully, False otherwise
        """

    @abstractmethod
    async def stop(self):
        """Stop the plugin.

        Called to stop the plugin's functionality cleanly.
        """

    @abstractmethod
    async def cleanup(self):
        """Clean up resources.

        Called when the plugin is being unloaded.
        """

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information.

        Returns:
            Dictionary with status information
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "version": self.metadata.version,
            "type": self.metadata.plugin_type,
            "category": self.metadata.category,
            "enabled": self._enabled,
        }


class TaskMonitorPlugin(Plugin):
    """Base class for task monitoring plugins.

    Task monitoring plugins provide different ways to monitor Semaphore tasks
    (polling, webhooks, etc.). Only one task monitor plugin can be active at a time.
    """

    def __init__(self, bot: Any, config: Dict[str, Any], metadata: PluginMetadata):
        super().__init__(bot, config, metadata)
        self.monitoring_active = False

    @abstractmethod
    async def monitor_task(
        self,
        project_id: int,
        task_id: int,
        room_id: str,
        task_name: Optional[str],
        sender: Optional[str] = None,
    ):
        """Monitor a specific task.

        Args:
            project_id: Semaphore project ID
            task_id: Task ID to monitor
            room_id: Matrix room ID for notifications
            task_name: Optional task name
            sender: Optional sender user ID for personalized notifications
        """

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status with monitoring info."""
        status = super().get_status()
        status["monitoring_active"] = self.monitoring_active
        return status


class PluginManager:
    """Manages loading, initialization, and lifecycle of plugins."""

    def __init__(self, bot: Any, config: Dict[str, Any], plugins_dir: str = "plugins"):
        """Initialize plugin manager.

        Args:
            bot: Reference to the ChatrixBot instance
            config: Bot configuration
            plugins_dir: Directory containing plugins
        """
        self.bot = bot
        self.config = config
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.disabled_plugins: Dict[str, PluginMetadata] = {}
        self.task_monitor: Optional[TaskMonitorPlugin] = None

    def discover_plugins(self) -> List[Path]:
        """Discover available plugins in the plugins directory.

        Returns:
            List of paths to plugin directories
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return []

        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "meta.json").exists():
                plugins.append(item)

        logger.info(f"Discovered {len(plugins)} plugins: {[p.name for p in plugins]}")
        return plugins

    def load_plugin_metadata(self, plugin_dir: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from meta.json.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            PluginMetadata instance or None if loading failed
        """
        meta_file = plugin_dir / "meta.json"
        try:
            with open(meta_file, "r") as f:
                data = json.load(f)

            metadata = PluginMetadata(data, plugin_dir)
            logger.debug(
                f"Loaded metadata for plugin: {metadata.name} v{metadata.version}"
            )
            return metadata

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {meta_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading metadata from {meta_file}: {e}")
            return None

    def load_plugin_config(
        self, plugin_dir: Path, metadata: PluginMetadata
    ) -> Dict[str, Any]:
        """Load plugin configuration from plugin.json file.

        Args:
            plugin_dir: Path to plugin directory
            metadata: Plugin metadata

        Returns:
            Plugin configuration dictionary
        """
        config_file = plugin_dir / "plugin.json"
        plugin_config = {}

        # Try to load plugin.json
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    import hjson

                    plugin_config = hjson.load(f)
                logger.debug(
                    f"Loaded configuration for plugin '{metadata.name}' from {config_file}"
                )
            except Exception as e:
                logger.warning(f"Failed to load configuration from {config_file}: {e}")

        # Override with config from main config.json if present (for backwards compatibility)
        main_config_override = self.config.get("plugins", {}).get(metadata.name, {})
        if main_config_override:
            logger.debug(
                f"Applying configuration overrides for plugin '{metadata.name}' from main config"
            )
            plugin_config.update(main_config_override)

        return plugin_config

    def load_plugin_module(
        self, plugin_dir: Path, metadata: PluginMetadata
    ) -> Optional[Type[Plugin]]:
        """Load the plugin Python module.

        Args:
            plugin_dir: Path to plugin directory
            metadata: Plugin metadata

        Returns:
            Plugin class or None if loading failed
        """
        plugin_file = plugin_dir / "plugin.py"
        if not plugin_file.exists():
            logger.error(f"Plugin file not found: {plugin_file}")
            return None

        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"chatrixcd_plugin_{metadata.name}", plugin_file
            )
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {plugin_file}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find the plugin class (should inherit from Plugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin
                    and attr is not TaskMonitorPlugin
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error(f"No Plugin subclass found in {plugin_file}")
                return None

            logger.debug(f"Loaded plugin class: {plugin_class.__name__}")
            return plugin_class

        except Exception as e:
            logger.error(
                f"Error loading plugin module from {plugin_file}: {e}",
                exc_info=True,
            )
            return None

    async def load_plugin(self, plugin_dir: Path) -> bool:
        """Load a single plugin.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            True if loaded successfully, False otherwise
        """
        # Load metadata
        metadata = self.load_plugin_metadata(plugin_dir)
        if metadata is None:
            return False

        # Load the plugin module
        plugin_class = self.load_plugin_module(plugin_dir, metadata)
        if plugin_class is None:
            return False

        # Get plugin-specific configuration from plugin.json
        plugin_config = self.load_plugin_config(plugin_dir, metadata)

        # Instantiate the plugin
        try:
            plugin = plugin_class(self.bot, plugin_config, metadata)

            # Initialize the plugin
            if not await plugin.initialize():
                logger.error(f"Failed to initialize plugin '{metadata.name}'")
                return False

            # Store the plugin
            self.loaded_plugins[metadata.name] = plugin
            self.plugin_metadata[metadata.name] = metadata

            # Track task monitor plugins separately
            if isinstance(plugin, TaskMonitorPlugin):
                self.task_monitor = plugin
                logger.info(
                    f"Loaded task monitor plugin: {metadata.name} v{metadata.version}"
                )
            else:
                logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")

            return True

        except Exception as e:
            logger.error(
                f"Error instantiating plugin '{metadata.name}': {e}",
                exc_info=True,
            )
            return False

    async def load_all_plugins(self) -> int:
        """Load all available plugins.

        Returns:
            Number of plugins loaded successfully
        """
        logger.info("Loading plugins...")

        plugins = self.discover_plugins()
        if not plugins:
            logger.warning("No plugins found")
            return 0

        loaded_count = 0
        for plugin_dir in plugins:
            metadata = self.load_plugin_metadata(plugin_dir)
            if metadata is None:
                continue

            # Load config to check enabled
            plugin_config = self.load_plugin_config(plugin_dir, metadata)
            enabled = plugin_config.get("enabled", metadata.enabled)

            if enabled:
                # Enforce mutual exclusion: only one TaskMonitorPlugin may be loaded
                if (
                    metadata.plugin_type == "task_monitor"
                    and self.task_monitor is not None
                ):
                    logger.info(
                        f"Skipping task monitor plugin '{metadata.name}' because '{self.task_monitor.metadata.name}' is already active"
                    )
                    # Track as disabled due to mutual exclusion
                    self.disabled_plugins[metadata.name] = metadata
                    continue

                if await self.load_plugin(plugin_dir):
                    loaded_count += 1
            else:
                self.disabled_plugins[metadata.name] = metadata
                logger.info(f"Plugin '{metadata.name}' is disabled")

        logger.info(f"Loaded {loaded_count}/{len(plugins)} plugins")

        # Check if a task monitor plugin is loaded
        if self.task_monitor is None:
            logger.warning(
                "No task monitor plugin loaded. Task monitoring will not be available. "
                "Please enable either 'semaphore_poll' or 'semaphore_webhook' plugin."
            )

        return loaded_count

    async def start_plugins(self):
        """Start all loaded plugins."""
        logger.info("Starting plugins...")

        for name, plugin in self.loaded_plugins.items():
            try:
                if await plugin.start():
                    logger.info(f"Started plugin: {name}")
                else:
                    logger.error(f"Failed to start plugin: {name}")
            except Exception as e:
                logger.error(f"Error starting plugin '{name}': {e}", exc_info=True)

    async def stop_plugins(self):
        """Stop all loaded plugins."""
        logger.info("Stopping plugins...")

        for name, plugin in self.loaded_plugins.items():
            try:
                await plugin.stop()
                logger.info(f"Stopped plugin: {name}")
            except Exception as e:
                logger.error(f"Error stopping plugin '{name}': {e}", exc_info=True)

    async def cleanup_plugins(self):
        """Clean up all loaded plugins."""
        logger.info("Cleaning up plugins...")

        for name, plugin in self.loaded_plugins.items():
            try:
                await plugin.cleanup()
                logger.debug(f"Cleaned up plugin: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin '{name}': {e}", exc_info=True)

        self.loaded_plugins.clear()
        self.plugin_metadata.clear()
        self.task_monitor = None

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self.loaded_plugins.get(name)

    def get_all_plugins_status(self) -> List[Dict[str, Any]]:
        """Get status information for all loaded plugins.

        Returns:
            List of plugin status dictionaries
        """
        return [plugin.get_status() for plugin in self.loaded_plugins.values()]

    def get_task_monitor(self) -> Optional[TaskMonitorPlugin]:
        """Get the active task monitor plugin.

        Returns:
            TaskMonitorPlugin instance or None if none loaded
        """
        return self.task_monitor
