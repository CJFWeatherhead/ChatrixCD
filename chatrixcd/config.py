"""Configuration management for ChatrixCD bot."""

import hjson
import os
import logging
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path


# Current configuration schema version
CURRENT_CONFIG_VERSION = 3


class ConfigMigrator:
    """Handles migration of configuration files between versions."""
    
    @staticmethod
    def migrate(config: Dict[str, Any], from_version: int) -> Dict[str, Any]:
        """Migrate configuration from one version to another.
        
        Args:
            config: Configuration dictionary to migrate
            from_version: Current version of the configuration
            
        Returns:
            Migrated configuration dictionary
        """
        logger = logging.getLogger(__name__)
        
        # Apply migrations sequentially
        current_version = from_version
        while current_version < CURRENT_CONFIG_VERSION:
            next_version = current_version + 1
            migration_method = getattr(
                ConfigMigrator, 
                f'_migrate_v{current_version}_to_v{next_version}',
                None
            )
            
            if migration_method:
                logger.info(f"Migrating configuration from v{current_version} to v{next_version}")
                config = migration_method(config)
            else:
                logger.warning(f"No migration method found for v{current_version} to v{next_version}")
            
            current_version = next_version
        
        # Set the version in the config
        config['_config_version'] = CURRENT_CONFIG_VERSION
        return config
    
    @staticmethod
    def _migrate_v1_to_v2(config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 1 (no version) to version 2.
        
        Changes in v2:
        - Added _config_version field
        - Added bot.greetings_enabled (default: true)
        - Added bot.greeting_rooms (default: [])
        - Added bot.startup_message and bot.shutdown_message
        """
        # These fields are already handled by defaults in load_config
        # This migration exists primarily to set the version number
        # and document the changes between versions
        return config
    
    @staticmethod
    def _migrate_v2_to_v3(config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 2 to version 3.
        
        Changes in v3:
        - Added semaphore.ssl_ca_cert, ssl_client_cert, ssl_client_key (now standard features)
        - Added bot.log_file for configurable log file path
        """
        # These fields are already handled by defaults in load_config
        # SSL settings were already in the default config but are now documented as part of v3
        # This migration exists primarily to set the version number
        # and document the changes between versions
        return config


class Config:
    """Configuration class for the bot.
    
    Configuration priority (highest to lowest):
    1. Configuration file values (highest priority - explicit values in JSON/HJSON file)
    2. Hardcoded defaults (lowest priority - used when not in config file)
    
    Configuration is loaded only from the configuration file (config.json by default).
    Environment variables are no longer supported to simplify configuration management.
    """

    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration from file.
        
        Supports JSON and HJSON (Human JSON with comments) configuration files.
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration with clear priority: hardcoded defaults < file."""
        logger = logging.getLogger(__name__)
        
        # Step 1: Start with hardcoded defaults
        self.config = self._get_default_config()
        
        # Step 2: Load and merge configuration file if it exists (highest priority)
        if os.path.exists(self.config_file):
            file_config = self._load_config_file()
            
            # Check version and migrate if necessary
            config_version = file_config.get('_config_version', 1)
            
            if config_version < CURRENT_CONFIG_VERSION:
                logger.info(f"Migrating configuration from v{config_version} to v{CURRENT_CONFIG_VERSION}")
                file_config = ConfigMigrator.migrate(file_config, config_version)
                self._save_migrated_config(file_config)
            elif config_version > CURRENT_CONFIG_VERSION:
                logger.warning(
                    f"Configuration version {config_version} is newer than supported v{CURRENT_CONFIG_VERSION}. "
                    "Some features may not work correctly."
                )
            
            # Merge file config (file values override defaults)
            self.config = self._deep_merge(self.config, file_config)
        else:
            logger.warning(f"Configuration file '{self.config_file}' not found, using defaults only")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get hardcoded default configuration (no environment variables).
        
        Returns:
            Dictionary with default configuration values
        """
        return {
            '_config_version': CURRENT_CONFIG_VERSION,
            'matrix': {
                'homeserver': 'https://matrix.org',
                'user_id': '',
                'device_id': 'CHATRIXCD',
                'device_name': 'ChatrixCD Bot',
                'auth_type': 'password',
                'password': '',
                'oidc_redirect_url': 'http://localhost:8080/callback',
                'store_path': './store',
            },
            'semaphore': {
                'url': '',
                'api_token': '',
                'ssl_verify': True,
                'ssl_ca_cert': '',
                'ssl_client_cert': '',
                'ssl_client_key': '',
            },
            'bot': {
                'command_prefix': '!cd',
                'allowed_rooms': [],
                'admin_users': [],
                'greetings_enabled': True,
                'greeting_rooms': [],
                'startup_message': '🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!',
                'shutdown_message': '👋 ChatrixCD bot is shutting down. See you later!',
                'log_file': 'chatrixcd.log',
                'tui_mode': 'turbo',  # Options: 'turbo' (new Turbo Vision style) or 'classic' (original TUI)
            },
        }
    

    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration file (JSON or HJSON with comments).
        
        Returns:
            Configuration dictionary from file
            
        Raises:
            SystemExit: If file cannot be parsed or read
        """
        logger = logging.getLogger(__name__)
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    # Use hjson which supports both JSON and HJSON (JSON with comments)
                    config = hjson.loads(content)
                    logger.debug(f"Loaded configuration from '{self.config_file}'")
                    return dict(config) if config else {}
                except hjson.HjsonDecodeError as e:
                    error_msg = f"Failed to parse configuration file '{self.config_file}'"
                    error_msg += f"\n  Error: {e}"
                    logger.error(error_msg)
                    print(f"\nERROR: {error_msg}\n", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    error_msg = f"Failed to parse configuration file '{self.config_file}'"
                    error_msg += f"\n  Error: {e}"
                    logger.error(error_msg)
                    print(f"\nERROR: {error_msg}\n", file=sys.stderr)
                    sys.exit(1)
        except FileNotFoundError:
            error_msg = f"Configuration file '{self.config_file}' not found"
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            error_msg = f"Failed to read configuration file '{self.config_file}': {e}"
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}\n", file=sys.stderr)
            sys.exit(1)
    
    def _save_migrated_config(self, config: Dict[str, Any]) -> None:
        """Save migrated configuration back to disk.
        
        Args:
            config: Migrated configuration to save
        """
        logger = logging.getLogger(__name__)
        file_path = Path(self.config_file)
        
        # Create backup of original file
        backup_path = file_path.with_suffix('.backup')
        
        try:
            if backup_path.exists():
                # If backup already exists, append timestamp
                import time
                timestamp = int(time.time())
                backup_path = Path(str(file_path) + f'.backup.{timestamp}')
            
            # Copy original to backup
            import shutil
            shutil.copy2(self.config_file, backup_path)
            logger.info(f"Created backup of original configuration at '{backup_path}'")
            
            # Save migrated config as HJSON (more human-readable with comments support)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(hjson.dumps(config, indent=2))
            
            logger.info(f"Saved migrated configuration to '{self.config_file}'")
        except Exception as e:
            logger.warning(f"Failed to save migrated configuration: {e}")
            # Non-fatal - we can continue with the in-memory migrated config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override values taking precedence.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        import copy
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if value is None:
                # Skip None values - keep base value
                continue
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override the value (including empty strings)
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
    
    def validate_schema(self) -> List[str]:
        """Validate configuration schema and return list of errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required matrix fields
        matrix_config = self.get_matrix_config()
        if not matrix_config.get('homeserver'):
            errors.append("matrix.homeserver is required")
        if not matrix_config.get('user_id'):
            errors.append("matrix.user_id is required")
        
        # Check authentication configuration
        auth_type = matrix_config.get('auth_type', 'password')
        if auth_type == 'password' and not matrix_config.get('password'):
            errors.append("matrix.password is required when auth_type is 'password'")
        elif auth_type == 'oidc':
            # OIDC only requires auth_type to be set to 'oidc'
            # oidc_redirect_url is optional with a sensible default
            pass
        elif auth_type not in ['password', 'oidc']:
            errors.append(f"matrix.auth_type must be 'password' or 'oidc', got '{auth_type}'")
        
        # Check required semaphore fields
        semaphore_config = self.get_semaphore_config()
        if not semaphore_config.get('url'):
            errors.append("semaphore.url is required")
        if not semaphore_config.get('api_token'):
            errors.append("semaphore.api_token is required")
        
        # Check bot configuration
        bot_config = self.get_bot_config()
        if not bot_config.get('command_prefix'):
            errors.append("bot.command_prefix is required")
        
        return errors
    
    def get_config_version(self) -> int:
        """Get the configuration version.
        
        Returns:
            Configuration version number
        """
        return self.config.get('_config_version', 1)
