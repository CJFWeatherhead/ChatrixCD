"""Tests for configuration module."""

import os
import tempfile
import unittest
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


if __name__ == '__main__':
    unittest.main()
