"""Tests for configuration module."""

import os
import tempfile
import unittest
import sys
import json
from io import StringIO
from chatrixcd.config import Config, ConfigMigrator, CURRENT_CONFIG_VERSION


class TestConfig(unittest.TestCase):
    """Test configuration loading and management."""

    def test_environment_variables_ignored(self):
        """Test that environment variables are ignored (no longer supported)."""
        os.environ['MATRIX_HOMESERVER'] = 'https://test.matrix.org'
        os.environ['MATRIX_USER_ID'] = '@testbot:test.matrix.org'
        os.environ['MATRIX_PASSWORD'] = 'testpass'
        os.environ['SEMAPHORE_URL'] = 'https://semaphore.test.com'
        os.environ['SEMAPHORE_API_TOKEN'] = 'testtoken'
        
        config = Config('nonexistent.json')
        
        # Environment variables should be ignored, defaults should be used
        self.assertEqual(config.get('matrix.homeserver'), 'https://matrix.org')
        self.assertEqual(config.get('matrix.user_id'), '')
        self.assertEqual(config.get('matrix.password'), '')
        self.assertEqual(config.get('semaphore.url'), '')
        self.assertEqual(config.get('semaphore.api_token'), '')
        
        # Clean up
        del os.environ['MATRIX_HOMESERVER']
        del os.environ['MATRIX_USER_ID']
        del os.environ['MATRIX_PASSWORD']
        del os.environ['SEMAPHORE_URL']
        del os.environ['SEMAPHORE_API_TOKEN']

    def test_default_values(self):
        """Test default configuration values."""
        config = Config('nonexistent.json')
        
        self.assertEqual(config.get('matrix.device_id'), 'CHATRIXCD')
        self.assertEqual(config.get('matrix.auth_type'), 'password')
        self.assertEqual(config.get('bot.command_prefix'), '!cd')



    def test_get_with_default(self):
        """Test get method with default value."""
        config = Config('nonexistent.json')
        
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
        self.assertIsNone(config.get('nonexistent.key'))

    def test_unreadable_config_file(self):
        """Test graceful handling of unreadable config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"matrix": {"homeserver": "test"}}, f)
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
        config = Config('nonexistent.json')
        
        # Test default greeting configuration
        self.assertTrue(config.get('bot.greetings_enabled'))
        self.assertEqual(config.get('bot.greeting_rooms'), [])
        self.assertIsNotNone(config.get('bot.startup_message'))
        self.assertIsNotNone(config.get('bot.shutdown_message'))

    def test_greeting_config_from_json(self):
        """Test greeting configuration from JSON file."""
        json_content = {
            "bot": {
                "greetings_enabled": False,
                "greeting_rooms": ["!room1:example.com", "!room2:example.com"],
                "startup_message": "Custom startup message",
                "shutdown_message": "Custom shutdown message"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            self.assertFalse(config.get('bot.greetings_enabled'))
            self.assertEqual(config.get('bot.greeting_rooms'), ['!room1:example.com', '!room2:example.com'])
            self.assertEqual(config.get('bot.startup_message'), 'Custom startup message')
            self.assertEqual(config.get('bot.shutdown_message'), 'Custom shutdown message')
        finally:
            os.unlink(temp_file)

    def test_greeting_config_from_env_ignored(self):
        """Test that greeting configuration from environment variables is ignored."""
        os.environ['BOT_GREETINGS_ENABLED'] = 'false'
        os.environ['BOT_GREETING_ROOMS'] = '!room1:example.com,!room2:example.com'
        os.environ['BOT_STARTUP_MESSAGE'] = 'Env startup message'
        os.environ['BOT_SHUTDOWN_MESSAGE'] = 'Env shutdown message'
        
        config = Config('nonexistent.json')
        
        # Environment variables should be ignored, defaults should be used
        self.assertTrue(config.get('bot.greetings_enabled'))
        self.assertEqual(config.get('bot.greeting_rooms'), [])
        self.assertEqual(config.get('bot.startup_message'), '🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!')
        self.assertEqual(config.get('bot.shutdown_message'), '👋 ChatrixCD bot is shutting down. See you later!')
        
        # Clean up
        del os.environ['BOT_GREETINGS_ENABLED']
        del os.environ['BOT_GREETING_ROOMS']
        del os.environ['BOT_STARTUP_MESSAGE']
        del os.environ['BOT_SHUTDOWN_MESSAGE']

    def test_json_config_with_missing_fields_uses_defaults(self):
        """Test that JSON config without all fields still gets defaults."""
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.example.test",
                "user_id": "@bot:example.com",
                "access_token": "test_token"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            matrix_config = config.get_matrix_config()
            
            # JSON values should be present
            self.assertEqual(matrix_config.get('homeserver'), 'https://matrix.example.test')
            self.assertEqual(matrix_config.get('user_id'), '@bot:example.com')
            self.assertEqual(matrix_config.get('access_token'), 'test_token')
            
            # Missing fields should have defaults
            self.assertEqual(matrix_config.get('device_id'), 'CHATRIXCD')
            self.assertEqual(matrix_config.get('device_name'), 'ChatrixCD Bot')
            self.assertEqual(matrix_config.get('store_path'), './store')
            self.assertEqual(matrix_config.get('auth_type'), 'password')
            
            # Verify all required fields are present (not None)
            self.assertIsNotNone(matrix_config.get('device_id'))
            self.assertIsNotNone(matrix_config.get('device_name'))
            self.assertIsNotNone(matrix_config.get('store_path'))
            self.assertIsNotNone(matrix_config.get('auth_type'))
        finally:
            os.unlink(temp_file)

    def test_oidc_auth_config_from_json(self):
        """Test OIDC authentication configuration from JSON."""
        json_content = {
            "matrix": {
                "homeserver": "https://mymatrixserver.com",
                "user_id": "@auser:mymatrixserver",
                "auth_type": "oidc",
                "oidc_redirect_url": "http://localhost:8080/callback"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            matrix_config = config.get_matrix_config()
            
            # User specified values
            self.assertEqual(matrix_config.get('homeserver'), 'https://mymatrixserver.com')
            self.assertEqual(matrix_config.get('user_id'), '@auser:mymatrixserver')
            self.assertEqual(matrix_config.get('auth_type'), 'oidc')
            self.assertEqual(matrix_config.get('oidc_redirect_url'), 'http://localhost:8080/callback')
            
            # Defaults for unspecified values
            self.assertEqual(matrix_config.get('device_id'), 'CHATRIXCD')
            self.assertEqual(matrix_config.get('device_name'), 'ChatrixCD Bot')
            self.assertEqual(matrix_config.get('store_path'), './store')
            
            # Ensure user_id is not None or empty
            self.assertIsNotNone(matrix_config.get('user_id'))
            self.assertTrue(matrix_config.get('user_id'))
        finally:
            os.unlink(temp_file)


    def test_json_config(self):
        """Test configuration from JSON file."""
        json_content = {
            "matrix": {
                "homeserver": "https://json.matrix.org",
                "user_id": "@jsonbot:json.matrix.org",
                "auth_type": "password",
                "password": "jsonpassword"
            },
            "semaphore": {
                "url": "https://json.semaphore.com",
                "api_token": "jsontoken123"
            },
            "bot": {
                "command_prefix": "!json"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            self.assertEqual(config.get('matrix.homeserver'), 'https://json.matrix.org')
            self.assertEqual(config.get('matrix.user_id'), '@jsonbot:json.matrix.org')
            self.assertEqual(config.get('matrix.auth_type'), 'password')
            self.assertEqual(config.get('matrix.password'), 'jsonpassword')
            self.assertEqual(config.get('semaphore.url'), 'https://json.semaphore.com')
            self.assertEqual(config.get('bot.command_prefix'), '!json')
            
            # Check that defaults are still applied
            self.assertEqual(config.get('matrix.device_id'), 'CHATRIXCD')
        finally:
            os.unlink(temp_file)
    
    def test_malformed_json(self):
        """Test graceful handling of malformed JSON."""
        json_content = '{"matrix": {"homeserver": "test", "unclosed": }'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            temp_file = f.name
        
        try:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            
            with self.assertRaises(SystemExit) as cm:
                Config(temp_file)
            
            self.assertEqual(cm.exception.code, 1)
            
            error_output = sys.stderr.getvalue()
            self.assertIn('Failed to parse configuration file', error_output)
            self.assertIn(temp_file, error_output)
            
            sys.stderr = old_stderr
        finally:
            os.unlink(temp_file)
    
    def test_config_version_detection(self):
        """Test configuration version detection."""
        # Test v2 config (will be migrated to v3)
        json_content = {
            "_config_version": 2,
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            # v2 config should be migrated to v3 (current version)
            self.assertEqual(config.get_config_version(), 3)
        finally:
            os.unlink(temp_file)
    
    def test_config_migration_v1_to_v2(self):
        """Test migration from v1 (no version) to v2."""
        # Old config without version field
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "password": "test"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            # Should have been migrated to current version
            self.assertEqual(config.get_config_version(), CURRENT_CONFIG_VERSION)
            
            # Original data should be preserved
            self.assertEqual(config.get('matrix.homeserver'), 'https://matrix.org')
            self.assertEqual(config.get('matrix.user_id'), '@bot:matrix.org')
            
            # v2 fields should have defaults
            self.assertTrue(config.get('bot.greetings_enabled'))
            self.assertEqual(config.get('bot.greeting_rooms'), [])
            self.assertIsNotNone(config.get('bot.startup_message'))
            self.assertIsNotNone(config.get('bot.shutdown_message'))
        finally:
            os.unlink(temp_file)
            # Clean up backup file if created
            backup_file = temp_file + '.backup'
            if os.path.exists(backup_file):
                os.unlink(backup_file)
    
    def test_config_validation_success(self):
        """Test configuration validation with valid config."""
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "password": "testpass"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            },
            "bot": {
                "command_prefix": "!cd"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            errors = config.validate_schema()
            self.assertEqual(errors, [])
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_missing_required_fields(self):
        """Test configuration validation with missing required fields."""
        json_content = {
            "matrix": {
                "homeserver": "",
                "user_id": ""
            },
            "semaphore": {
                "url": "",
                "api_token": ""
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            errors = config.validate_schema()
            
            # Should have multiple validation errors
            self.assertGreater(len(errors), 0)
            self.assertTrue(any('homeserver' in e for e in errors))
            self.assertTrue(any('user_id' in e for e in errors))
            self.assertTrue(any('semaphore.url' in e for e in errors))
            self.assertTrue(any('api_token' in e for e in errors))
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_token_auth_deprecated(self):
        """Test validation fails when token auth is used (deprecated)."""
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "auth_type": "token"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            errors = config.validate_schema()
            
            # Should fail because token auth is no longer supported
            self.assertTrue(any('auth_type' in e and 'token' in e for e in errors))
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_oidc_auth_valid(self):
        """Test validation succeeds for OIDC authentication."""
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "auth_type": "oidc"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            errors = config.validate_schema()
            
            # OIDC validation should pass without requiring oidc_issuer, oidc_client_id, oidc_client_secret
            self.assertEqual(errors, [])
        finally:
            os.unlink(temp_file)
    
    def test_config_validation_invalid_auth_type(self):
        """Test validation fails with invalid auth type."""
        json_content = {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "auth_type": "invalid"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            errors = config.validate_schema()
            
            self.assertTrue(any('auth_type' in e and 'invalid' in e for e in errors))
        finally:
            os.unlink(temp_file)
    
    def test_json_with_version(self):
        """Test JSON config with version field."""
        json_content = {
            "_config_version": 2,
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "password": "test"
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            # v2 config should be migrated to v3 (current version)
            self.assertEqual(config.get_config_version(), 3)
            self.assertEqual(config.get('matrix.homeserver'), 'https://matrix.org')
        finally:
            os.unlink(temp_file)


    def test_hjson_with_comments(self):
        """Test HJSON configuration with comments."""
        hjson_content = '''
        {
            // This is a comment
            "_config_version": 2,
            "matrix": {
                "homeserver": "https://hjson.matrix.org",  // Server URL
                "user_id": "@hjsonbot:hjson.matrix.org",
                /* Multi-line comment
                   for auth type */
                "auth_type": "token",
                "access_token": "hjson_token_123"
            },
            "semaphore": {
                "url": "https://hjson.semaphore.com",
                "api_token": "hjson_api_token"
            },
            "bot": {
                "command_prefix": "!hjson"  # Python-style comment also works
            }
        }
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(hjson_content)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            # Verify values were parsed correctly despite comments
            self.assertEqual(config.get('matrix.homeserver'), 'https://hjson.matrix.org')
            self.assertEqual(config.get('matrix.user_id'), '@hjsonbot:hjson.matrix.org')
            self.assertEqual(config.get('matrix.auth_type'), 'token')
            self.assertEqual(config.get('matrix.access_token'), 'hjson_token_123')
            self.assertEqual(config.get('semaphore.url'), 'https://hjson.semaphore.com')
            self.assertEqual(config.get('bot.command_prefix'), '!hjson')
            
            # Check that defaults are still applied
            self.assertEqual(config.get('matrix.device_id'), 'CHATRIXCD')
        finally:
            os.unlink(temp_file)
    
    def test_hjson_trailing_commas(self):
        """Test HJSON with trailing commas (not valid in strict JSON)."""
        hjson_content = '''
        {
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "@bot:matrix.org",
                "password": "test",  // Trailing comma is OK in HJSON
            },
            "semaphore": {
                "url": "https://semaphore.test",
                "api_token": "token",  // Another trailing comma
            },
        }
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(hjson_content)
            temp_file = f.name
        
        try:
            config = Config(temp_file)
            
            # Verify values were parsed correctly despite trailing commas
            self.assertEqual(config.get('matrix.homeserver'), 'https://matrix.org')
            self.assertEqual(config.get('matrix.user_id'), '@bot:matrix.org')
            self.assertEqual(config.get('semaphore.url'), 'https://semaphore.test')
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
