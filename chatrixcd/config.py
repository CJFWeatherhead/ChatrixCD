"""Configuration management for ChatrixCD bot."""

import hjson
import os
import logging
import sys
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path


# Current configuration schema version
CURRENT_CONFIG_VERSION = 5


class ConfigMigrator:
    """Handles migration of configuration files between versions.

    Configuration version history:
    - v1: Initial configuration
    - v2: Added greetings_enabled, greeting_rooms, startup_message, shutdown_message
    - v3: Added SSL certificate options, log_file configuration
    - v4: Added TUI mode options, mouse support, color settings, verbosity
    - v5: Added plugin system with load_plugins control, moved plugins config to separate files

    All migrations are handled by default values in Config class.
    This migrator only updates the version number.
    """

    @staticmethod
    def migrate(config: Dict[str, Any], from_version: int) -> Dict[str, Any]:
        """Migrate configuration to current version.

        Args:
            config: Configuration dictionary to migrate
            from_version: Current version of the configuration

        Returns:
            Migrated configuration dictionary with updated version
        """
        logger = logging.getLogger(__name__)

        if from_version < CURRENT_CONFIG_VERSION:
            logger.info(
                f"Migrating configuration from v{from_version} to v{CURRENT_CONFIG_VERSION}"
            )
            config["_config_version"] = CURRENT_CONFIG_VERSION

        return config


class Config:
    """Configuration class for the bot.

    Configuration priority (highest to lowest):
    1. Configuration file values (highest priority - explicit values in JSON/HJSON file)
    2. Hardcoded defaults (lowest priority - used when not in config file)

    Configuration is loaded only from the configuration file (config.json by default).
    Environment variables are no longer supported to simplify configuration management.
    """

    def __init__(
        self, config_file: str = "config.json", auto_reload: bool = False
    ):
        """Initialize configuration from file.

        Supports JSON and HJSON (Human JSON with comments) configuration files.

        Args:
            config_file: Path to configuration file
            auto_reload: If True, automatically reload config when file changes
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.auto_reload = auto_reload
        self._last_mtime: Optional[float] = None
        self._reload_task: Optional[Any] = (
            None  # asyncio.Task, but avoid import
        )

        self.load_config()

        # Start auto-reload if requested
        if auto_reload:
            self.start_auto_reload()

    def load_config(self):
        """Load configuration with clear priority: hardcoded defaults < file."""
        logger = logging.getLogger(__name__)

        # Step 1: Start with hardcoded defaults
        self.config = self._get_default_config()

        # Step 2: Load and merge configuration file if it exists (highest priority)
        if os.path.exists(self.config_file):
            file_config = self._load_config_file()

            # Check version and migrate if necessary
            config_version = file_config.get("_config_version", 1)

            if config_version < CURRENT_CONFIG_VERSION:
                logger.info(
                    "Configuration version %s detected, current version is %s",
                    config_version,
                    CURRENT_CONFIG_VERSION,
                )
                logger.info(
                    "Automatically migrating configuration to new version..."
                )
                file_config = ConfigMigrator.migrate(
                    file_config, config_version
                )
                self._save_migrated_config(file_config)
                logger.info(
                    "Configuration migrated and saved. You may want to run 'chatrixcd --init' to review new settings."
                )
            elif config_version > CURRENT_CONFIG_VERSION:
                logger.warning(
                    f"Configuration version {config_version} is newer than supported v{CURRENT_CONFIG_VERSION}. "
                    "Some features may not work correctly."
                )

            # Merge file config (file values override defaults)
            self.config = self._deep_merge(self.config, file_config)

            # Update last modified time
            try:
                self._last_mtime = os.path.getmtime(self.config_file)
            except Exception:
                pass
        else:
            logger.warning(
                "Configuration file '%s' not found, using defaults only",
                self.config_file,
            )

    def _get_default_config(self) -> Dict[str, Any]:
        """Get hardcoded default configuration (no environment variables).

        Returns:
            Dictionary with default configuration values
        """
        return {
            "_config_version": CURRENT_CONFIG_VERSION,
            "matrix": {
                "homeserver": "https://matrix.org",
                "user_id": "",
                "device_id": "CHATRIXCD",
                "device_name": "ChatrixCD Bot",
                "auth_type": "password",
                "password": "",
                "oidc_redirect_url": "http://localhost:8080/callback",
                "store_path": "./store",
            },
            "semaphore": {
                "url": "",
                "api_token": "",
                "ssl_verify": True,
                "ssl_ca_cert": "",
                "ssl_client_cert": "",
                "ssl_client_key": "",
            },
            "bot": {
                "command_prefix": "!cd",
                "allowed_rooms": [],
                "admin_users": [],
                "greetings_enabled": True,
                "greeting_rooms": [],
                "startup_message": "🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!",
                "shutdown_message": "👋 ChatrixCD bot is shutting down. See you later!",
                "log_file": "chatrixcd.log",
                "mouse_enabled": False,  # Enable mouse support in TUI
                "color_enabled": False,  # Enable colored output
                "color_theme": "default",  # Theme: 'default', 'midnight', 'grayscale', 'windows31', 'msdos'
                "verbosity": "info",  # Verbosity: 'silent', 'error', 'info', 'debug'
                "load_plugins": True,  # Enable/disable plugin loading
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
            with open(self.config_file, "r", encoding="utf-8") as f:
                content = f.read()
                try:
                    # Use hjson which supports both JSON and HJSON (JSON with comments)
                    config = hjson.loads(content)
                    logger.debug(
                        f"Loaded configuration from '{self.config_file}'"
                    )
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
            error_msg = (
                f"Failed to read configuration file '{self.config_file}': {e}"
            )
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
        backup_path = file_path.with_suffix(".backup")

        try:
            if backup_path.exists():
                # If backup already exists, append timestamp
                import time

                timestamp = int(time.time())
                backup_path = Path(str(file_path) + f".backup.{timestamp}")

            # Copy original to backup
            import shutil

            shutil.copy2(self.config_file, backup_path)
            logger.info(
                f"Created backup of original configuration at '{backup_path}'"
            )

            # Save migrated config as HJSON (more human-readable with comments support)
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(hjson.dumps(config, indent=2))

            logger.info(
                f"Saved migrated configuration to '{self.config_file}'"
            )
        except Exception as e:
            logger.warning(f"Failed to save migrated configuration: {e}")
            # Non-fatal - we can continue with the in-memory migrated config

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
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

            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override the value (including empty strings)
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def get_matrix_config(self) -> Dict[str, Any]:
        """Get Matrix configuration."""
        return self.config.get("matrix", {})

    def get_semaphore_config(self) -> Dict[str, Any]:
        """Get Semaphore configuration."""
        return self.config.get("semaphore", {})

    def get_bot_config(self) -> Dict[str, Any]:
        """Get bot configuration."""
        return self.config.get("bot", {})

    def validate_schema(self) -> List[str]:
        """Validate configuration schema and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required matrix fields
        matrix_config = self.get_matrix_config()
        if not matrix_config.get("homeserver"):
            errors.append("matrix.homeserver is required")
        if not matrix_config.get("user_id"):
            errors.append("matrix.user_id is required")

        # Check authentication configuration
        auth_type = matrix_config.get("auth_type", "password")
        if auth_type == "password" and not matrix_config.get("password"):
            errors.append(
                "matrix.password is required when auth_type is 'password'"
            )
        elif auth_type == "oidc":
            # OIDC only requires auth_type to be set to 'oidc'
            # oidc_redirect_url is optional with a sensible default
            pass
        elif auth_type not in ["password", "oidc"]:
            errors.append(
                f"matrix.auth_type must be 'password' or 'oidc', got '{auth_type}'"
            )

        # Check required semaphore fields
        semaphore_config = self.get_semaphore_config()
        if not semaphore_config.get("url"):
            errors.append("semaphore.url is required")
        if not semaphore_config.get("api_token"):
            errors.append("semaphore.api_token is required")

        # Check bot configuration
        bot_config = self.get_bot_config()
        if not bot_config.get("command_prefix"):
            errors.append("bot.command_prefix is required")

        return errors

    def get_config_version(self) -> int:
        """Get the configuration version.

        Returns:
            Configuration version number
        """
        return self.config.get("_config_version", 1)

    def check_for_changes(self) -> bool:
        """Check if the config file has been modified.

        Returns:
            True if file has been modified, False otherwise
        """
        if not os.path.exists(self.config_file):
            return False

        try:
            current_mtime = os.path.getmtime(self.config_file)
            if self._last_mtime is None or current_mtime > self._last_mtime:
                return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to check file modification time: {e}")

        return False

    def start_auto_reload(self):
        """Start automatic reloading of config when file changes."""
        logger = logging.getLogger(__name__)
        try:
            # Only start if we have a running event loop
            asyncio.get_running_loop()
            if self._reload_task is None or self._reload_task.done():
                self._reload_task = asyncio.create_task(
                    self._auto_reload_loop()
                )
                logger.info("Started auto-reload for config file")
        except RuntimeError:
            # No event loop running, will start later when needed
            logger.debug(
                "No event loop available yet, auto-reload will start when bot runs"
            )

    def stop_auto_reload(self):
        """Stop automatic reloading."""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            logger = logging.getLogger(__name__)
            logger.info("Stopped auto-reload for config file")

    async def _auto_reload_loop(self):
        """Background task that checks for file changes and reloads."""
        logger = logging.getLogger(__name__)
        try:
            while True:
                await asyncio.sleep(
                    10
                )  # Check every 10 seconds (less frequent for config)

                if self.check_for_changes():
                    logger.info(
                        f"Config file '{self.config_file}' has been modified, reloading..."
                    )
                    self.load_config()
                    logger.info("Configuration reloaded successfully")

        except asyncio.CancelledError:
            logger.debug("Auto-reload task cancelled")
        except Exception as e:
            logger.error(f"Error in auto-reload loop: {e}")
