"""Tests for aliases plugin."""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock
from chatrixcd.plugin_manager import PluginMetadata
from plugins.aliases.plugin import AliasesPlugin


class TestAliasesPlugin(unittest.IsolatedAsyncioTestCase):
    """Test the aliases plugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.aliases_file = os.path.join(self.temp_dir, "aliases.json")

        # Create mock bot and metadata
        self.mock_bot = Mock()
        self.mock_metadata = PluginMetadata(
            {
                "name": "aliases",
                "description": "Test plugin",
                "version": "1.0.0",
                "author": "Test",
                "type": "generic",
                "category": "core",
                "enabled": True,
                "dependencies": [],
                "python_dependencies": [],
            },
            Path("/tmp"),
        )

        # Plugin config
        self.config = {
            "enabled": True,
            "aliases_file": self.aliases_file,
            "auto_reload": False,  # Disable for testing
            "reserved_commands": [
                "help",
                "projects",
                "templates",
                "run",
                "status",
                "stop",
                "logs",
                "ping",
                "info",
                "pet",
                "scold",
                "admins",
                "rooms",
                "exit",
                "aliases",
            ],
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        if os.path.exists(self.aliases_file):
            os.remove(self.aliases_file)
        os.rmdir(self.temp_dir)

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        self.assertEqual(plugin.aliases_file, self.aliases_file)
        self.assertEqual(plugin.auto_reload, False)
        self.assertIsInstance(plugin.reserved_commands, list)
        self.assertEqual(plugin.aliases, {})

    async def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        # Test initialize
        result = await plugin.initialize()
        self.assertTrue(result)

        # Test start
        result = await plugin.start()
        self.assertTrue(result)

        # Test stop
        await plugin.stop()

        # Test cleanup
        await plugin.cleanup()

    def test_load_aliases_nonexistent_file(self):
        """Test loading aliases from a file that doesn't exist."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.load_aliases()

        self.assertEqual(plugin.aliases, {})

    def test_load_aliases_empty_file(self):
        """Test loading aliases from an empty file."""
        # Create empty file
        open(self.aliases_file, "w").close()

        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.load_aliases()

        self.assertEqual(plugin.aliases, {})

    def test_load_aliases_valid_json(self):
        """Test loading aliases from valid JSON file."""
        test_aliases = {"deploy": "run 1 5", "status": "status 123"}

        with open(self.aliases_file, "w") as f:
            json.dump(test_aliases, f)

        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.load_aliases()

        self.assertEqual(plugin.aliases, test_aliases)

    def test_load_aliases_invalid_json(self):
        """Test loading aliases from invalid JSON file."""
        # Create invalid JSON
        with open(self.aliases_file, "w") as f:
            f.write("{invalid json}")

        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.load_aliases()

        self.assertEqual(plugin.aliases, {})

    def test_save_aliases(self):
        """Test saving aliases to file."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"test": "run 1 2"}

        result = plugin.save_aliases()
        self.assertTrue(result)

        # Verify file was written
        self.assertTrue(os.path.exists(self.aliases_file))
        with open(self.aliases_file, "r") as f:
            saved_aliases = json.load(f)
        self.assertEqual(saved_aliases, {"test": "run 1 2"})

    def test_resolve_alias_exists(self):
        """Test resolving an alias that exists."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"deploy": "run 1 5"}

        result = plugin.resolve_alias("deploy")
        self.assertEqual(result, "run 1 5")

    def test_resolve_alias_not_exists(self):
        """Test resolving an alias that doesn't exist."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"deploy": "run 1 5"}

        result = plugin.resolve_alias("nonexistent")
        self.assertEqual(result, "nonexistent")

    def test_add_alias_valid(self):
        """Test adding a valid alias."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.add_alias("deploy", "run 1 5")
        self.assertTrue(result)
        self.assertEqual(plugin.aliases["deploy"], "run 1 5")

    def test_add_alias_accepts_prefixed(self):
        """Test adding an alias with a prefixed command normalizes correctly."""
        cfg = dict(self.config)
        cfg["command_prefix"] = "!cd"
        plugin = AliasesPlugin(self.mock_bot, cfg, self.mock_metadata)

        result = plugin.add_alias("petme", "!cd pet")
        self.assertTrue(result)
        # Stored without prefix
        self.assertEqual(plugin.aliases["petme"], "pet")

    def test_resolve_alias_appends_args(self):
        """Test resolving alias keeps extra arguments appended."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"deploy": "run 4 5"}

        resolved = plugin.resolve_alias("deploy --tags=something --arg=\"--dry-run\"")
        self.assertEqual(resolved, "run 4 5 --tags=something --arg=\"--dry-run\"")

    def test_add_alias_reserved_command(self):
        """Test adding an alias with a reserved command name."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.add_alias("help", "run 1 5")
        self.assertFalse(result)
        self.assertNotIn("help", plugin.aliases)

    def test_remove_alias_exists(self):
        """Test removing an alias that exists."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"deploy": "run 1 5"}

        result = plugin.remove_alias("deploy")
        self.assertTrue(result)
        self.assertNotIn("deploy", plugin.aliases)

    def test_remove_alias_not_exists(self):
        """Test removing an alias that doesn't exist."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.remove_alias("nonexistent")
        self.assertFalse(result)

    def test_list_aliases(self):
        """Test listing all aliases."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"deploy": "run 1 5", "test": "run 2 3"}

        aliases = plugin.list_aliases()
        expected = {"deploy": "run 1 5", "test": "run 2 3"}
        self.assertEqual(aliases, expected)
        # Ensure it's a copy, not the original dict
        self.assertIsNot(aliases, plugin.aliases)

    def test_validate_command_valid(self):
        """Test validating a valid command."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.validate_command("run 1 5")
        self.assertTrue(result)

    def test_validate_command_invalid(self):
        """Test validating an invalid command."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.validate_command("invalid_command")
        self.assertFalse(result)

    def test_validate_command_empty(self):
        """Test validating an empty command."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)

        result = plugin.validate_command("")
        self.assertFalse(result)

    def test_get_status(self):
        """Test getting plugin status."""
        plugin = AliasesPlugin(self.mock_bot, self.config, self.mock_metadata)
        plugin.aliases = {"test": "run 1 2"}

        status = plugin.get_status()

        expected_keys = [
            "name",
            "version",
            "enabled",
            "aliases_count",
            "aliases_file",
            "auto_reload",
        ]
        for key in expected_keys:
            self.assertIn(key, status)

        self.assertEqual(status["name"], "aliases")
        self.assertEqual(status["aliases_count"], 1)
        self.assertEqual(status["aliases_file"], self.aliases_file)
        self.assertEqual(status["auto_reload"], False)


if __name__ == "__main__":
    unittest.main()
