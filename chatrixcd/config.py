"""Configuration management for ChatrixCD bot."""

import yaml
import os
import logging
import sys
from typing import Optional, Dict, Any


class Config:
    """Configuration class for the bot."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize configuration from file or environment variables."""
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file."""
        logger = logging.getLogger(__name__)
        
        # Start with defaults - always use these as base
        defaults = {
            'matrix': {
                'homeserver': os.getenv('MATRIX_HOMESERVER', 'https://matrix.org'),
                'user_id': os.getenv('MATRIX_USER_ID', ''),
                'device_id': os.getenv('MATRIX_DEVICE_ID', 'CHATRIXCD'),
                'device_name': os.getenv('MATRIX_DEVICE_NAME', 'ChatrixCD Bot'),
                'auth_type': os.getenv('MATRIX_AUTH_TYPE', 'password'),  # 'password' or 'token'
                'password': os.getenv('MATRIX_PASSWORD', ''),
                'access_token': os.getenv('MATRIX_ACCESS_TOKEN', ''),
                'oidc_issuer': os.getenv('MATRIX_OIDC_ISSUER', ''),
                'oidc_client_id': os.getenv('MATRIX_OIDC_CLIENT_ID', ''),
                'oidc_client_secret': os.getenv('MATRIX_OIDC_CLIENT_SECRET', ''),
                'store_path': os.getenv('MATRIX_STORE_PATH', './store'),
            },
            'semaphore': {
                'url': os.getenv('SEMAPHORE_URL', ''),
                'api_token': os.getenv('SEMAPHORE_API_TOKEN', ''),
            },
            'bot': {
                'command_prefix': os.getenv('BOT_COMMAND_PREFIX', '!cd'),
                'allowed_rooms': os.getenv('BOT_ALLOWED_ROOMS', '').split(',') if os.getenv('BOT_ALLOWED_ROOMS') else [],
                'admin_users': os.getenv('BOT_ADMIN_USERS', '').split(',') if os.getenv('BOT_ADMIN_USERS') else [],
                'greetings_enabled': os.getenv('BOT_GREETINGS_ENABLED', 'true').lower() in ('true', '1', 'yes'),
                'greeting_rooms': os.getenv('BOT_GREETING_ROOMS', '').split(',') if os.getenv('BOT_GREETING_ROOMS') else [],
                'startup_message': os.getenv('BOT_STARTUP_MESSAGE', '🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!'),
                'shutdown_message': os.getenv('BOT_SHUTDOWN_MESSAGE', '👋 ChatrixCD bot is shutting down. See you later!'),
            },
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    yaml_config = yaml.safe_load(f) or {}
                
                # Merge YAML config with defaults
                # YAML values override defaults, but defaults fill in missing values
                self.config = self._merge_configs(defaults, yaml_config)
            except yaml.YAMLError as e:
                error_msg = f"Failed to parse YAML configuration file '{self.config_file}'"
                
                # Extract detailed error information
                if hasattr(e, 'problem_mark'):
                    mark = e.problem_mark
                    error_msg += f"\n  Error at line {mark.line + 1}, column {mark.column + 1}"
                
                if hasattr(e, 'problem'):
                    error_msg += f"\n  Problem: {e.problem}"
                
                if hasattr(e, 'context'):
                    error_msg += f"\n  Context: {e.context}"
                
                logger.error(error_msg)
                print(f"\nERROR: {error_msg}\n", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                error_msg = f"Failed to read configuration file '{self.config_file}': {e}"
                logger.error(error_msg)
                print(f"\nERROR: {error_msg}\n", file=sys.stderr)
                sys.exit(1)
        else:
            # No config file, use defaults (which include environment variables)
            self.config = defaults
    
    def _merge_configs(self, defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries, with overrides taking precedence.
        
        Args:
            defaults: Default configuration values
            overrides: Override values from YAML file
            
        Returns:
            Merged configuration dictionary
        """
        result = defaults.copy()
        
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override the value
                result[key] = value
        
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def get_matrix_config(self) -> Dict[str, Any]:
        """Get Matrix configuration."""
        return self.config.get('matrix', {})

    def get_semaphore_config(self) -> Dict[str, Any]:
        """Get Semaphore configuration."""
        return self.config.get('semaphore', {})

    def get_bot_config(self) -> Dict[str, Any]:
        """Get bot configuration."""
        return self.config.get('bot', {})
