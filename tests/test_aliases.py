"""Tests for alias manager module."""

import unittest
import os
import tempfile
import json
from chatrixcd.aliases import AliasManager


class TestAliasManager(unittest.TestCase):
    """Test AliasManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary file for aliases
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.alias_manager = AliasManager(self.temp_file.name)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_init(self):
        """Test alias manager initialization."""
        self.assertEqual(self.alias_manager.aliases_file, self.temp_file.name)
        self.assertEqual(self.alias_manager.aliases, {})

    def test_add_alias(self):
        """Test adding an alias."""
        result = self.alias_manager.add_alias('deploy', 'run 1 5')
        self.assertTrue(result)
        self.assertEqual(self.alias_manager.get_alias('deploy'), 'run 1 5')

    def test_add_alias_reserved_command(self):
        """Test adding alias with reserved command name."""
        result = self.alias_manager.add_alias('help', 'run 1 5')
        self.assertFalse(result)
        self.assertIsNone(self.alias_manager.get_alias('help'))

    def test_remove_alias(self):
        """Test removing an alias."""
        self.alias_manager.add_alias('test', 'status 123')
        result = self.alias_manager.remove_alias('test')
        self.assertTrue(result)
        self.assertIsNone(self.alias_manager.get_alias('test'))

    def test_remove_nonexistent_alias(self):
        """Test removing an alias that doesn't exist."""
        result = self.alias_manager.remove_alias('nonexistent')
        self.assertFalse(result)

    def test_get_alias(self):
        """Test getting an alias."""
        self.alias_manager.add_alias('myalias', 'templates 3')
        alias = self.alias_manager.get_alias('myalias')
        self.assertEqual(alias, 'templates 3')

    def test_get_nonexistent_alias(self):
        """Test getting an alias that doesn't exist."""
        alias = self.alias_manager.get_alias('nonexistent')
        self.assertIsNone(alias)

    def test_list_aliases(self):
        """Test listing all aliases."""
        self.alias_manager.add_alias('alias1', 'run 1 1')
        self.alias_manager.add_alias('alias2', 'status')
        aliases = self.alias_manager.list_aliases()
        self.assertEqual(len(aliases), 2)
        self.assertIn('alias1', aliases)
        self.assertIn('alias2', aliases)

    def test_resolve_command_with_alias(self):
        """Test resolving a command with an alias."""
        self.alias_manager.add_alias('deploy', 'run 1 5')
        resolved = self.alias_manager.resolve_command('deploy')
        self.assertEqual(resolved, 'run 1 5')

    def test_resolve_command_with_alias_and_args(self):
        """Test resolving a command with an alias and additional arguments."""
        self.alias_manager.add_alias('mytemplates', 'templates')
        resolved = self.alias_manager.resolve_command('mytemplates 3')
        self.assertEqual(resolved, 'templates 3')

    def test_resolve_command_without_alias(self):
        """Test resolving a command without an alias."""
        resolved = self.alias_manager.resolve_command('projects')
        self.assertEqual(resolved, 'projects')

    def test_validate_command_valid(self):
        """Test validating a valid command."""
        self.assertTrue(AliasManager.validate_command('run 1 5'))
        self.assertTrue(AliasManager.validate_command('status 123'))
        self.assertTrue(AliasManager.validate_command('logs'))
        self.assertTrue(AliasManager.validate_command('ping'))
        self.assertTrue(AliasManager.validate_command('info'))

    def test_validate_command_invalid(self):
        """Test validating an invalid command."""
        self.assertFalse(AliasManager.validate_command('invalid'))
        self.assertFalse(AliasManager.validate_command(''))
        self.assertFalse(AliasManager.validate_command('notacommand 123'))

    def test_save_and_load_aliases(self):
        """Test saving and loading aliases from file."""
        self.alias_manager.add_alias('alias1', 'run 1 1')
        self.alias_manager.add_alias('alias2', 'status')
        
        # Create new alias manager with same file
        new_manager = AliasManager(self.temp_file.name)
        
        # Should have loaded the aliases
        self.assertEqual(len(new_manager.aliases), 2)
        self.assertEqual(new_manager.get_alias('alias1'), 'run 1 1')
        self.assertEqual(new_manager.get_alias('alias2'), 'status')

    def test_load_nonexistent_file(self):
        """Test loading aliases from a file that doesn't exist."""
        # Should not raise an error
        manager = AliasManager('nonexistent_file.json')
        self.assertEqual(manager.aliases, {})

    def test_load_invalid_json(self):
        """Test loading aliases from invalid JSON file."""
        # Write invalid JSON to file
        with open(self.temp_file.name, 'w') as f:
            f.write('{ invalid json }')
        
        # Should handle gracefully
        manager = AliasManager(self.temp_file.name)
        self.assertEqual(manager.aliases, {})


if __name__ == '__main__':
    unittest.main()
