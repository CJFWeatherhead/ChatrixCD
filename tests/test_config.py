"""Tests for configuration module."""

import os
import tempfile
import unittest
import sys
from io import StringIO
from chatrixcd.config import Config


class TestConfig(unittest.TestCase):
    """Test configuration loading and management."""

    def test_environment_variables(self):
        """Test configuration from environment variables."""
        os.environ['MATRIX_HOMESERVER'] = 'https://test.matrix.org'
        os.environ['MATRIX_USER_ID'] = '@testbot:test.matrix.org'
        os.environ['MATRIX_PASSWORD'] = 'testpass'
        os.environ['SEMAPHORE_URL'] = 'https://semaphore.test.com'
        os.environ['SEMAPHORE_API_TOKEN'] = 'testtoken'
        
        config = Config('nonexistent.yaml')
        
        self.assertEqual(config.get('matrix.homeserver'), 'https://test.matrix.org')
        self.assertEqual(config.get('matrix.user_id'), '@testbot:test.matrix.org')
        self.assertEqual(config.get('matrix.password'), 'testpass')
        self.assertEqual(config.get('semaphore.url'), 'https://semaphore.test.com')
        self.assertEqual(config.get('semaphore.api_token'), 'testtoken')

    def test_default_values(self):
        """Test default configuration values."""
        config = Config('nonexistent.yaml')
        
        self.assertEqual(config.get('matrix.device_id'), 'CHATRIXCD')
        self.assertEqual(config.get('matrix.auth_type'), 'password')
        self.assertEqual(config.get('bot.command_prefix'), '!cd')

    def test_yaml_config(self):
        """Test configuration from YAML file."""
        yaml_content = """
matrix:
  homeserver: "https://yaml.matrix.org"
  user_id: "@yamlbot:yaml.matrix.org"
  auth_type: "token"
  access_token: "yamltoken"

semaphore:
  url: "https://yaml.semaphore.com"
  api_token: "yamltoken123"

bot:
  command_prefix: "!yaml"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            self.assertEqual(config.get('matrix.homeserver'), 'https://yaml.matrix.org')
            self.assertEqual(config.get('matrix.user_id'), '@yamlbot:yaml.matrix.org')
            self.assertEqual(config.get('matrix.auth_type'), 'token')
            self.assertEqual(config.get('matrix.access_token'), 'yamltoken')
            self.assertEqual(config.get('semaphore.url'), 'https://yaml.semaphore.com')
            self.assertEqual(config.get('bot.command_prefix'), '!yaml')
        finally:
            os.unlink(temp_file)

    def test_get_with_default(self):
        """Test get method with default value."""
        config = Config('nonexistent.yaml')
        
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
        self.assertIsNone(config.get('nonexistent.key'))

    def test_malformed_yaml_missing_quote(self):
        """Test graceful handling of malformed YAML with missing quote."""
        yaml_content = """
matrix:
  homeserver: "https://matrix.org"
  password: "unclosed
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            # Capture stderr to check error message
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            # This should exit with code 1
            with self.assertRaises(SystemExit) as cm:
                Config(temp_file)
            
            self.assertEqual(cm.exception.code, 1)
            
            # Check that error message contains useful information
            error_output = sys.stderr.getvalue()
            self.assertIn('Failed to parse YAML', error_output)
            self.assertIn(temp_file, error_output)
            self.assertIn('line', error_output.lower())
            
            sys.stderr = old_stderr
        finally:
            os.unlink(temp_file)

    def test_malformed_yaml_unclosed_bracket(self):
        """Test graceful handling of malformed YAML with unclosed bracket."""
        yaml_content = """
matrix:
  homeserver: "https://matrix.org"
  list: [item1, item2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            with self.assertRaises(SystemExit) as cm:
                Config(temp_file)
            
            self.assertEqual(cm.exception.code, 1)
            
            error_output = sys.stderr.getvalue()
            self.assertIn('Failed to parse YAML', error_output)
            self.assertIn(temp_file, error_output)
            
            sys.stderr = old_stderr
        finally:
            os.unlink(temp_file)

    def test_malformed_yaml_invalid_indentation(self):
        """Test graceful handling of malformed YAML with invalid indentation."""
        yaml_content = """
matrix:
  homeserver: "https://matrix.org"
 user_id: "@bot:matrix.org"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            with self.assertRaises(SystemExit) as cm:
                Config(temp_file)
            
            self.assertEqual(cm.exception.code, 1)
            
            error_output = sys.stderr.getvalue()
            self.assertIn('Failed to parse YAML', error_output)
            
            sys.stderr = old_stderr
        finally:
            os.unlink(temp_file)

    def test_unreadable_config_file(self):
        """Test graceful handling of unreadable config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("matrix:\n  homeserver: test\n")
            temp_file = f.name
        
        try:
            # Make file unreadable
            os.chmod(temp_file, 0o000)
            
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            with self.assertRaises(SystemExit) as cm:
                Config(temp_file)
            
            self.assertEqual(cm.exception.code, 1)
            
            error_output = sys.stderr.getvalue()
            self.assertIn('Failed to read configuration file', error_output)
            self.assertIn(temp_file, error_output)
            
            sys.stderr = old_stderr
        finally:
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_greeting_config_defaults(self):
        """Test default values for greeting configuration."""
        config = Config('nonexistent.yaml')
        
        # Test default greeting configuration
        self.assertTrue(config.get('bot.greetings_enabled'))
        self.assertEqual(config.get('bot.greeting_rooms'), [])
        self.assertIsNotNone(config.get('bot.startup_message'))
        self.assertIsNotNone(config.get('bot.shutdown_message'))

    def test_greeting_config_from_yaml(self):
        """Test greeting configuration from YAML file."""
        yaml_content = """
bot:
  greetings_enabled: false
  greeting_rooms:
    - "!room1:example.com"
    - "!room2:example.com"
  startup_message: "Custom startup message"
  shutdown_message: "Custom shutdown message"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            self.assertFalse(config.get('bot.greetings_enabled'))
            self.assertEqual(config.get('bot.greeting_rooms'), ['!room1:example.com', '!room2:example.com'])
            self.assertEqual(config.get('bot.startup_message'), 'Custom startup message')
            self.assertEqual(config.get('bot.shutdown_message'), 'Custom shutdown message')
        finally:
            os.unlink(temp_file)

    def test_greeting_config_from_env(self):
        """Test greeting configuration from environment variables."""
        os.environ['BOT_GREETINGS_ENABLED'] = 'false'
        os.environ['BOT_GREETING_ROOMS'] = '!room1:example.com,!room2:example.com'
        os.environ['BOT_STARTUP_MESSAGE'] = 'Env startup message'
        os.environ['BOT_SHUTDOWN_MESSAGE'] = 'Env shutdown message'
        
        config = Config('nonexistent.yaml')
        
        self.assertFalse(config.get('bot.greetings_enabled'))
        self.assertEqual(config.get('bot.greeting_rooms'), ['!room1:example.com', '!room2:example.com'])
        self.assertEqual(config.get('bot.startup_message'), 'Env startup message')
        self.assertEqual(config.get('bot.shutdown_message'), 'Env shutdown message')
        
        # Clean up
        del os.environ['BOT_GREETINGS_ENABLED']
        del os.environ['BOT_GREETING_ROOMS']
        del os.environ['BOT_STARTUP_MESSAGE']
        del os.environ['BOT_SHUTDOWN_MESSAGE']


if __name__ == '__main__':
    unittest.main()
