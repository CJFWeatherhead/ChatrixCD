"""Configuration wizard for ChatrixCD bot.

This module provides interactive configuration setup for ChatrixCD,
supporting both console and TUI modes.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List


def parse_config_example() -> Dict[str, Any]:
    """Parse config.json.example to extract field descriptions and defaults.

    Returns:
        Dictionary mapping config keys to their descriptions and defaults
    """
    example_file = Path(__file__).parent.parent / "config.json.example"

    if not example_file.exists():
        return {}

    field_info = {}

    try:
        with open(example_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_comment = []
        for i, line in enumerate(lines):
            stripped = line.strip()

            # Collect comments
            if stripped.startswith("//"):
                comment = stripped[2:].strip()
                current_comment.append(comment)
            # When we hit a key-value pair, associate the comments with it
            elif (
                ":" in stripped
                and not stripped.startswith("{")
                and not stripped.startswith("}")
            ):
                # Extract key
                key = stripped.split(":")[0].strip().strip('"')

                # Extract default value
                value_part = ":".join(stripped.split(":")[1:]).strip()
                # Remove trailing comma
                if value_part.endswith(","):
                    value_part = value_part[:-1].strip()

                # Store field info
                if current_comment:
                    field_info[key] = {
                        "description": " ".join(current_comment),
                        "default": value_part.strip('"').strip("'"),
                    }
                current_comment = []
            # Reset comments on blank lines or structural markers
            elif not stripped or stripped in ["{", "}"]:
                current_comment = []
    except Exception as e:
        print(
            f"Warning: Could not parse config.json.example: {e}",
            file=sys.stderr,
        )

    return field_info


def get_console_input(
    prompt: str, default: str = "", is_password: bool = False
) -> str:
    """Get input from console with optional default.

    Args:
        prompt: Prompt to display
        default: Default value if user presses enter
        is_password: If True, hide input (not implemented in basic version)

    Returns:
        User input or default
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        value = input(full_prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguration cancelled.")
        sys.exit(0)


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from console.

    Args:
        prompt: Prompt to display
        default: Default value

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    full_prompt = f"{prompt} [{default_str}]: "

    try:
        value = input(full_prompt).strip().lower()
        if not value:
            return default
        return value in ["y", "yes", "true", "1"]
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguration cancelled.")
        sys.exit(0)


def get_choice(prompt: str, choices: List[str], default: str = "") -> str:
    """Get a choice from a list of options.

    Args:
        prompt: Prompt to display
        choices: List of valid choices
        default: Default choice

    Returns:
        Selected choice
    """
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " (default)" if choice == default else ""
        print(f"  {i}. {choice}{marker}")

    while True:
        try:
            value = input(f"Enter choice [1-{len(choices)}]: ").strip()
            if not value and default:
                return default

            # Try numeric input
            try:
                idx = int(value) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass

            # Try text input
            if value in choices:
                return value

            print(
                f"Invalid choice. Please enter 1-{len(choices)} or one of: {', '.join(choices)}"
            )
        except (EOFError, KeyboardInterrupt):
            print("\nConfiguration cancelled.")
            sys.exit(0)


def get_list_input(prompt: str, example: str = "") -> List[str]:
    """Get a comma-separated list of values.

    Args:
        prompt: Prompt to display
        example: Example value to show

    Returns:
        List of values
    """
    if example:
        full_prompt = f"{prompt} (comma-separated, e.g., {example}): "
    else:
        full_prompt = f"{prompt} (comma-separated, or press Enter to skip): "

    try:
        value = input(full_prompt).strip()
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguration cancelled.")
        sys.exit(0)


def run_console_config_wizard(
    existing_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run interactive configuration wizard in console mode.

    Args:
        existing_config: Existing configuration to use as defaults

    Returns:
        New configuration dictionary
    """
    print("=" * 70)
    print("ChatrixCD Configuration Wizard")
    print("=" * 70)
    print("\nThis wizard will help you configure ChatrixCD.")
    print("Press Ctrl+C at any time to cancel.\n")

    # Start with defaults
    config = {"_config_version": 4, "matrix": {}, "semaphore": {}, "bot": {}}

    # Use existing config as base if provided
    if existing_config:
        config.update(existing_config)

    # Matrix Configuration
    print("\n" + "=" * 70)
    print("Matrix Configuration")
    print("=" * 70)

    config["matrix"]["homeserver"] = get_console_input(
        "Matrix homeserver URL",
        config.get("matrix", {}).get("homeserver", "https://matrix.org"),
    )

    config["matrix"]["user_id"] = get_console_input(
        "Bot user ID (e.g., @bot:example.com)",
        config.get("matrix", {}).get("user_id", ""),
    )

    config["matrix"]["device_id"] = get_console_input(
        "Device ID", config.get("matrix", {}).get("device_id", "CHATRIXCD")
    )

    config["matrix"]["device_name"] = get_console_input(
        "Device name",
        config.get("matrix", {}).get("device_name", "ChatrixCD Bot"),
    )

    auth_type = get_choice(
        "Authentication type:",
        ["password", "oidc"],
        config.get("matrix", {}).get("auth_type", "password"),
    )
    config["matrix"]["auth_type"] = auth_type

    if auth_type == "password":
        config["matrix"]["password"] = get_console_input(
            "Bot password", config.get("matrix", {}).get("password", "")
        )
    else:  # oidc
        config["matrix"]["oidc_redirect_url"] = get_console_input(
            "OIDC redirect URL",
            config.get("matrix", {}).get(
                "oidc_redirect_url", "http://localhost:8080/callback"
            ),
        )

    config["matrix"]["store_path"] = get_console_input(
        "Encryption store path",
        config.get("matrix", {}).get("store_path", "./store"),
    )

    # Semaphore Configuration
    print("\n" + "=" * 70)
    print("Semaphore Configuration")
    print("=" * 70)

    config["semaphore"]["url"] = get_console_input(
        "Semaphore UI URL", config.get("semaphore", {}).get("url", "")
    )

    config["semaphore"]["api_token"] = get_console_input(
        "Semaphore API token", config.get("semaphore", {}).get("api_token", "")
    )

    if get_yes_no("Configure SSL/TLS settings?", False):
        config["semaphore"]["ssl_verify"] = get_yes_no(
            "Verify SSL certificate?",
            config.get("semaphore", {}).get("ssl_verify", True),
        )

        config["semaphore"]["ssl_ca_cert"] = get_console_input(
            "Custom CA certificate path (optional)",
            config.get("semaphore", {}).get("ssl_ca_cert", ""),
        )

        config["semaphore"]["ssl_client_cert"] = get_console_input(
            "Client certificate path (optional)",
            config.get("semaphore", {}).get("ssl_client_cert", ""),
        )

        config["semaphore"]["ssl_client_key"] = get_console_input(
            "Client certificate key path (optional)",
            config.get("semaphore", {}).get("ssl_client_key", ""),
        )
    else:
        config["semaphore"]["ssl_verify"] = config.get("semaphore", {}).get(
            "ssl_verify", True
        )
        config["semaphore"]["ssl_ca_cert"] = config.get("semaphore", {}).get(
            "ssl_ca_cert", ""
        )
        config["semaphore"]["ssl_client_cert"] = config.get(
            "semaphore", {}
        ).get("ssl_client_cert", "")
        config["semaphore"]["ssl_client_key"] = config.get(
            "semaphore", {}
        ).get("ssl_client_key", "")

    # Bot Configuration
    print("\n" + "=" * 70)
    print("Bot Configuration")
    print("=" * 70)

    config["bot"]["command_prefix"] = get_console_input(
        "Command prefix", config.get("bot", {}).get("command_prefix", "!cd")
    )

    config["bot"]["admin_users"] = get_list_input(
        "Admin users (leave empty for all users)",
        "@admin:example.com, @admin2:example.com",
    ) or config.get("bot", {}).get("admin_users", [])

    config["bot"]["allowed_rooms"] = get_list_input(
        "Allowed rooms (leave empty for all rooms)",
        "!room1:example.com, !room2:example.com",
    ) or config.get("bot", {}).get("allowed_rooms", [])

    config["bot"]["greetings_enabled"] = get_yes_no(
        "Enable greeting messages?",
        config.get("bot", {}).get("greetings_enabled", True),
    )

    if config["bot"]["greetings_enabled"]:
        config["bot"]["greeting_rooms"] = get_list_input(
            "Greeting rooms (leave empty for all allowed rooms)",
            "!room1:example.com",
        ) or config.get("bot", {}).get("greeting_rooms", [])
    else:
        config["bot"]["greeting_rooms"] = []

    config["bot"]["tui_mode"] = get_choice(
        "TUI mode:",
        ["turbo", "classic"],
        config.get("bot", {}).get("tui_mode", "turbo"),
    )

    config["bot"]["color_theme"] = get_choice(
        "Color theme:",
        ["default", "midnight", "grayscale", "windows31", "msdos"],
        config.get("bot", {}).get("color_theme", "default"),
    )

    config["bot"]["mouse_enabled"] = get_yes_no(
        "Enable mouse support in TUI?",
        config.get("bot", {}).get("mouse_enabled", False),
    )

    config["bot"]["color_enabled"] = get_yes_no(
        "Enable colored output?",
        config.get("bot", {}).get("color_enabled", False),
    )

    config["bot"]["verbosity"] = get_choice(
        "Log verbosity:",
        ["silent", "error", "info", "debug"],
        config.get("bot", {}).get("verbosity", "info"),
    )

    config["bot"]["log_file"] = get_console_input(
        "Log file path", config.get("bot", {}).get("log_file", "chatrixcd.log")
    )

    # Messages
    config["bot"]["startup_message"] = get_console_input(
        "Startup message",
        config.get("bot", {}).get(
            "startup_message",
            "🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!",
        ),
    )

    config["bot"]["shutdown_message"] = get_console_input(
        "Shutdown message",
        config.get("bot", {}).get(
            "shutdown_message",
            "👋 ChatrixCD bot is shutting down. See you later!",
        ),
    )

    return config


def save_config(
    config: Dict[str, Any], config_file: str = "config.json"
) -> bool:
    """Save configuration to file.

    Args:
        config: Configuration dictionary
        config_file: Path to config file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create backup if file exists
        config_path = Path(config_file)
        if config_path.exists():
            backup_path = config_path.with_suffix(".backup")
            import shutil

            shutil.copy2(config_path, backup_path)
            print(f"\nBackup saved to: {backup_path}")

        # Write new config
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        print(f"\nConfiguration saved to: {config_file}")
        return True
    except Exception as e:
        print(f"\nERROR: Failed to save configuration: {e}", file=sys.stderr)
        return False
