"""Tests for plugin manager."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from chatrixcd.plugin_manager import (
    Plugin,
    PluginManager,
    PluginMetadata,
    TaskMonitorPlugin,
)


class MockPlugin(Plugin):
    """Mock plugin for testing."""

    def __init__(self, bot, config, metadata):
        super().__init__(bot, config, metadata)
        self.initialized = False
        self.started = False
        self.stopped = False
        self.cleaned_up = False

    async def initialize(self) -> bool:
        self.initialized = True
        return True

    async def start(self) -> bool:
        self.started = True
        return True

    async def stop(self):
        self.stopped = True

    async def cleanup(self):
        self.cleaned_up = True


class MockTaskMonitor(TaskMonitorPlugin):
    """Mock task monitor plugin for testing."""

    def __init__(self, bot, config, metadata):
        super().__init__(bot, config, metadata)
        self.initialized = False
        self.started = False
        self.stopped = False
        self.cleaned_up = False
        self.monitored_tasks = []

    async def initialize(self) -> bool:
        self.initialized = True
        return True

    async def start(self) -> bool:
        self.started = True
        return True

    async def stop(self):
        self.stopped = True

    async def cleanup(self):
        self.cleaned_up = True

    async def monitor_task(self, project_id, task_id, room_id, task_name):
        self.monitored_tasks.append(
            {
                "project_id": project_id,
                "task_id": task_id,
                "room_id": room_id,
                "task_name": task_name,
            }
        )


class TestPluginMetadata(unittest.TestCase):
    """Test plugin metadata loading."""

    def test_metadata_creation(self):
        """Test creating plugin metadata from dictionary."""
        data = {
            "name": "test_plugin",
            "description": "Test plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "type": "generic",
            "category": "test",
            "enabled": True,
            "dependencies": [],
            "python_dependencies": ["aiohttp>=3.9.0"],
        }

        metadata = PluginMetadata(data, Path("/tmp/test"))

        self.assertEqual(metadata.name, "test_plugin")
        self.assertEqual(metadata.description, "Test plugin")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.author, "Test Author")
        self.assertEqual(metadata.plugin_type, "generic")
        self.assertEqual(metadata.category, "test")
        self.assertTrue(metadata.enabled)
        self.assertEqual(len(metadata.python_dependencies), 1)

    def test_metadata_defaults(self):
        """Test metadata defaults for missing fields."""
        data = {}
        metadata = PluginMetadata(data, Path("/tmp/test"))

        self.assertEqual(metadata.name, "Unknown")
        self.assertEqual(metadata.description, "")
        self.assertEqual(metadata.version, "0.0.0")
        self.assertEqual(metadata.author, "Unknown")
        self.assertEqual(metadata.plugin_type, "generic")
        self.assertEqual(metadata.category, "general")
        self.assertTrue(metadata.enabled)


class TestPluginBase(unittest.TestCase):
    """Test base plugin classes."""

    def test_plugin_initialization(self):
        """Test plugin base class initialization."""
        bot = Mock()
        config = {"test": "value"}
        metadata = PluginMetadata({"name": "test"}, Path("/tmp"))

        plugin = MockPlugin(bot, config, metadata)

        self.assertEqual(plugin.bot, bot)
        self.assertEqual(plugin.config, config)
        self.assertEqual(plugin.metadata, metadata)
        self.assertIsNotNone(plugin.logger)

    def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        bot = Mock()
        config = {}
        metadata = PluginMetadata({"name": "test"}, Path("/tmp"))

        plugin = MockPlugin(bot, config, metadata)

        # Test lifecycle
        asyncio.run(plugin.initialize())
        self.assertTrue(plugin.initialized)

        asyncio.run(plugin.start())
        self.assertTrue(plugin.started)

        asyncio.run(plugin.stop())
        self.assertTrue(plugin.stopped)

        asyncio.run(plugin.cleanup())
        self.assertTrue(plugin.cleaned_up)

    def test_plugin_status(self):
        """Test plugin status method."""
        bot = Mock()
        config = {}
        metadata = PluginMetadata(
            {
                "name": "test",
                "version": "1.0.0",
                "type": "generic",
                "category": "test",
                "enabled": True,
            },
            Path("/tmp"),
        )

        plugin = MockPlugin(bot, config, metadata)
        status = plugin.get_status()

        self.assertEqual(status["name"], "test")
        self.assertEqual(status["version"], "1.0.0")
        self.assertEqual(status["type"], "generic")
        self.assertEqual(status["category"], "test")
        self.assertTrue(status["enabled"])


class TestTaskMonitorPlugin(unittest.TestCase):
    """Test task monitor plugin class."""

    def test_task_monitor_initialization(self):
        """Test task monitor plugin initialization."""
        bot = Mock()
        config = {}
        metadata = PluginMetadata({"name": "test", "type": "task_monitor"}, Path("/tmp"))

        monitor = MockTaskMonitor(bot, config, metadata)

        self.assertFalse(monitor.monitoring_active)
        self.assertEqual(len(monitor.monitored_tasks), 0)

    def test_task_monitor_lifecycle(self):
        """Test task monitor lifecycle."""
        bot = Mock()
        config = {}
        metadata = PluginMetadata({"name": "test", "type": "task_monitor"}, Path("/tmp"))

        monitor = MockTaskMonitor(bot, config, metadata)

        asyncio.run(monitor.initialize())
        asyncio.run(monitor.start())

        self.assertTrue(monitor.started)

        asyncio.run(monitor.stop())
        self.assertTrue(monitor.stopped)

    def test_task_monitor_status(self):
        """Test task monitor status includes monitoring_active."""
        bot = Mock()
        config = {}
        metadata = PluginMetadata({"name": "test", "type": "task_monitor"}, Path("/tmp"))

        monitor = MockTaskMonitor(bot, config, metadata)
        status = monitor.get_status()

        self.assertIn("monitoring_active", status)
        self.assertFalse(status["monitoring_active"])


class TestPluginManager(unittest.TestCase):
    """Test plugin manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = Path(self.temp_dir) / "plugins"
        self.plugins_dir.mkdir()

        self.bot = Mock()
        self.config = {}

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_test_plugin(self, name: str, plugin_type: str = "generic", enabled: bool = True):
        """Helper to create a test plugin."""
        plugin_dir = self.plugins_dir / name
        plugin_dir.mkdir()

        # Create meta.json
        meta = {
            "name": name,
            "description": f"Test plugin {name}",
            "version": "1.0.0",
            "author": "Test",
            "type": plugin_type,
            "category": "test",
            "enabled": enabled,
            "dependencies": [],
            "python_dependencies": [],
        }

        with open(plugin_dir / "meta.json", "w") as f:
            json.dump(meta, f)

        # Create plugin.py
        plugin_code = """
from chatrixcd.plugin_manager import Plugin, TaskMonitorPlugin

class TestPlugin(Plugin):
    async def initialize(self):
        return True
    async def start(self):
        return True
    async def stop(self):
        pass
    async def cleanup(self):
        pass

class TestMonitor(TaskMonitorPlugin):
    async def initialize(self):
        return True
    async def start(self):
        return True
    async def stop(self):
        pass
    async def cleanup(self):
        pass
    async def monitor_task(self, project_id, task_id, room_id, task_name):
        pass
"""

        with open(plugin_dir / "plugin.py", "w") as f:
            f.write(plugin_code)

        return plugin_dir

    def test_discover_plugins(self):
        """Test plugin discovery."""
        # Create test plugins
        self._create_test_plugin("plugin1")
        self._create_test_plugin("plugin2")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))
        plugins = manager.discover_plugins()

        self.assertEqual(len(plugins), 2)
        plugin_names = [p.name for p in plugins]
        self.assertIn("plugin1", plugin_names)
        self.assertIn("plugin2", plugin_names)

    def test_discover_no_plugins(self):
        """Test discovery with no plugins."""
        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))
        plugins = manager.discover_plugins()

        self.assertEqual(len(plugins), 0)

    def test_load_plugin_metadata(self):
        """Test loading plugin metadata."""
        plugin_dir = self._create_test_plugin("test_plugin")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))
        metadata = manager.load_plugin_metadata(plugin_dir)

        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.name, "test_plugin")
        self.assertEqual(metadata.version, "1.0.0")

    def test_load_plugin_metadata_invalid_json(self):
        """Test loading metadata with invalid JSON."""
        plugin_dir = self.plugins_dir / "bad_plugin"
        plugin_dir.mkdir()

        # Create invalid JSON
        with open(plugin_dir / "meta.json", "w") as f:
            f.write("{ invalid json }")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))
        metadata = manager.load_plugin_metadata(plugin_dir)

        self.assertIsNone(metadata)

    def test_load_disabled_plugin(self):
        """Test that disabled plugins are not loaded."""
        self._create_test_plugin("disabled_plugin", enabled=False)

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        loaded = asyncio.run(manager.load_all_plugins())

        self.assertEqual(loaded, 0)
        self.assertEqual(len(manager.loaded_plugins), 0)

    def test_task_monitor_mutual_exclusion(self):
        """Test that only one task monitor can be loaded."""
        self._create_test_plugin("monitor1", plugin_type="task_monitor")
        self._create_test_plugin("monitor2", plugin_type="task_monitor")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        loaded = asyncio.run(manager.load_all_plugins())

        # Only one should load
        self.assertEqual(loaded, 1)
        self.assertIsNotNone(manager.task_monitor)

    def test_get_plugin(self):
        """Test getting a loaded plugin by name."""
        self._create_test_plugin("test_plugin")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        asyncio.run(manager.load_all_plugins())

        plugin = manager.get_plugin("test_plugin")
        self.assertIsNotNone(plugin)

    def test_get_nonexistent_plugin(self):
        """Test getting a plugin that doesn't exist."""
        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        plugin = manager.get_plugin("nonexistent")
        self.assertIsNone(plugin)

    def test_get_all_plugins_status(self):
        """Test getting status for all plugins."""
        self._create_test_plugin("plugin1")
        self._create_test_plugin("plugin2")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        asyncio.run(manager.load_all_plugins())

        statuses = manager.get_all_plugins_status()
        self.assertEqual(len(statuses), 2)

    def test_cleanup_plugins(self):
        """Test plugin cleanup."""
        self._create_test_plugin("test_plugin")

        manager = PluginManager(self.bot, self.config, str(self.plugins_dir))

        asyncio.run(manager.load_all_plugins())

        self.assertEqual(len(manager.loaded_plugins), 1)

        asyncio.run(manager.cleanup_plugins())

        self.assertEqual(len(manager.loaded_plugins), 0)
        self.assertIsNone(manager.task_monitor)

    def test_plugin_init_signatures(self):
        """Test that all plugin classes have correct __init__ signatures."""
        import inspect
        from pathlib import Path

        # Get the plugins directory
        plugins_dir = Path(__file__).parent.parent / "plugins"

        if not plugins_dir.exists():
            self.skipTest("Plugins directory not found")

        # Create a plugin manager instance
        manager = PluginManager(self.bot, self.config, str(plugins_dir))

        # Discover plugin directories
        plugin_dirs = manager.discover_plugins()

        if not plugin_dirs:
            self.skipTest("No plugins found")

        for plugin_dir in plugin_dirs:
            with self.subTest(plugin_dir=plugin_dir.name):
                # Load plugin metadata
                metadata = manager.load_plugin_metadata(plugin_dir)
                if metadata is None:
                    continue

                # Load plugin class
                plugin_class = manager.load_plugin_module(plugin_dir, metadata)
                if plugin_class is None:
                    continue

                # Check __init__ signature
                init_signature = inspect.signature(plugin_class.__init__)
                params = list(init_signature.parameters.keys())

                # Should have exactly 4 parameters: self, bot, config, metadata
                self.assertEqual(
                    len(params),
                    4,
                    f"Plugin {plugin_dir.name} __init__ should have 4 parameters, got {len(params)}: {params}",
                )

                self.assertEqual(
                    params[0],
                    "self",
                    f"Plugin {plugin_dir.name} first parameter should be 'self', got '{params[0]}'",
                )

                self.assertEqual(
                    params[1],
                    "bot",
                    f"Plugin {plugin_dir.name} second parameter should be 'bot', got '{params[1]}'",
                )

                self.assertEqual(
                    params[2],
                    "config",
                    f"Plugin {plugin_dir.name} third parameter should be 'config', got '{params[2]}'",
                )

                self.assertEqual(
                    params[3],
                    "metadata",
                    f"Plugin {plugin_dir.name} fourth parameter should be 'metadata', got '{params[3]}'",
                )


if __name__ == "__main__":
    unittest.main()
