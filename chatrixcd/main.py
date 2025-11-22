"""Main entry point for ChatrixCD bot."""

import argparse
import asyncio
import logging
import os
import sys
from chatrixcd import __version_full__
from chatrixcd.config import Config
from chatrixcd.bot import ChatrixBot
from chatrixcd.redactor import SensitiveInfoRedactor, RedactingFilter


def setup_logging(
    verbosity: int = 0,
    color: bool = False,
    redact: bool = False,
    log_file: str = "chatrixcd.log",
    tui_mode: bool = False,
):
    """Setup logging configuration.

    Args:
        verbosity: Verbosity level (0=INFO, 1=DEBUG, 2+=detailed DEBUG)
        color: Enable colored logging output
        redact: Enable redaction of sensitive information
        log_file: Path to log file (default: chatrixcd.log)
        tui_mode: If True, only log to file (no console output to avoid TUI interference)
    """
    # Determine log level based on verbosity
    if verbosity == 0:
        level = logging.INFO
    elif verbosity == 1:
        level = logging.DEBUG
    else:
        level = logging.DEBUG

    # In TUI mode, only log to file (no console output)
    # This prevents logs from interfering with the TUI display
    if tui_mode:
        handlers = [logging.FileHandler(log_file)]
    # Setup format with optional color support for console mode
    elif color:
        try:
            import colorlog

            handler = colorlog.StreamHandler(sys.stdout)
            handler.setFormatter(
                colorlog.ColoredFormatter(
                    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    log_colors={
                        "DEBUG": "cyan",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "red,bg_white",
                    },
                )
            )
            handlers = [handler, logging.FileHandler(log_file)]
        except ImportError:
            # Fallback if colorlog not available
            handlers = [
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file),
            ]
    else:
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file),
        ]

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Add redaction filter if requested
    if redact:
        redactor = SensitiveInfoRedactor(enabled=True, colorize=color)
        redacting_filter = RedactingFilter(redactor)
        for handler in logging.root.handlers:
            handler.addFilter(redacting_filter)

    # Set even more verbose logging for key modules if verbosity >= 2
    if verbosity >= 2:
        logging.getLogger("nio").setLevel(logging.DEBUG)
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)


def parse_args():
    """Parse command-line arguments.

    Returns:
        Namespace object containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="chatrixcd",
        description="ChatrixCD - Matrix bot for CI/CD automation with Semaphore UI",
        epilog="For more information, visit: https://github.com/CJFWeatherhead/ChatrixCD",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"ChatrixCD {__version_full__}",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="Increase verbosity (-v for DEBUG, -vv for detailed DEBUG with library logs)",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.json",
        metavar="FILE",
        help="Path to configuration file (default: config.json)",
    )

    parser.add_argument(
        "-C",
        "--color",
        action="store_true",
        help="Enable colored logging output (requires colorlog package)",
    )

    parser.add_argument(
        "-D",
        "--daemon",
        action="store_true",
        help="Run in daemon mode (detach from terminal and run in background)",
    )

    parser.add_argument(
        "-s",
        "--show-config",
        action="store_true",
        dest="show_config",
        help="Display configuration and exit (credentials will be redacted)",
    )

    parser.add_argument(
        "-a",
        "--admin",
        action="append",
        dest="admin_users",
        metavar="USER",
        help="Add admin user (can be specified multiple times, e.g., -a @user1:matrix.org -a @user2:matrix.org)",
    )

    parser.add_argument(
        "-r",
        "--room",
        action="append",
        dest="allowed_rooms",
        metavar="ROOM",
        help="Add allowed room (can be specified multiple times, e.g., -r !room1:matrix.org -r !room2:matrix.org)",
    )

    parser.add_argument(
        "-R",
        "--redact",
        action="store_true",
        help="Redact sensitive information from logs (room names, usernames, IPs, tokens, etc.)",
    )

    parser.add_argument(
        "-L",
        "--log-only",
        action="store_true",
        dest="log_only",
        help="Run in classic log-only mode (no TUI, only show logs)",
    )

    parser.add_argument(
        "-m",
        "--mouse",
        action="store_true",
        help="Enable mouse support in TUI (default: disabled)",
    )

    parser.add_argument(
        "-N",
        "--no-greetings",
        action="store_true",
        dest="no_greetings",
        help="Skip greeting messages on startup/shutdown (useful for testing)",
    )

    parser.add_argument(
        "-I",
        "--init",
        action="store_true",
        dest="init_config",
        help="Initialize or re-initialize configuration file interactively",
    )

    return parser.parse_args()


def daemonize():
    """Daemonize the process (Unix/Linux only).

    Forks the process into the background and detaches from the terminal.
    """
    # Save the current working directory before daemonizing
    # so the bot can still access config files
    original_cwd = os.getcwd()

    try:
        pid = os.fork()
        if pid > 0:
            # Exit parent process
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #1 failed: {e}\n")
        sys.exit(1)

    # Decouple from parent environment
    # Don't change directory - keep the original working directory
    # os.chdir('/') would break access to config files
    os.setsid()
    os.umask(0)

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit second parent process
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #2 failed: {e}\n")
        sys.exit(1)

    # Return to original working directory
    os.chdir(original_cwd)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "r") as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(os.devnull, "a+") as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(os.devnull, "a+") as f:
        os.dup2(f.fileno(), sys.stderr.fileno())


def print_config(config: Config, redact_identifiers: bool = False):
    """Print configuration with redacted credentials.

    Args:
        config: Configuration object to print
        redact_identifiers: If True, also redact room IDs, user IDs, and other identifiers
    """
    import json
    import copy

    # Deep copy config to avoid modifying original
    config_dict = copy.deepcopy(config.config)

    # Redact sensitive fields
    sensitive_fields = [
        "password",
        "access_token",
        "api_token",
        "client_secret",
        "oidc_client_secret",
    ]

    # Additional fields to redact when redact_identifiers is enabled
    identifier_fields = [
        "user_id",
        "homeserver",
        "url",
        "admin_users",
        "allowed_rooms",
    ]

    def redact_sensitive(obj, path=""):
        """Recursively redact sensitive fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in sensitive_fields and value:
                    obj[key] = "***REDACTED***"
                elif redact_identifiers and key in identifier_fields and value:
                    if isinstance(value, str):
                        # Use redactor for proper redaction
                        redactor = SensitiveInfoRedactor(
                            enabled=True, colorize=False
                        )
                        obj[key] = redactor.redact(value)
                    elif isinstance(value, list):
                        redactor = SensitiveInfoRedactor(
                            enabled=True, colorize=False
                        )
                        obj[key] = [redactor.redact(str(v)) for v in value]
                else:
                    redact_sensitive(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for item in obj:
                redact_sensitive(item, path)

    redact_sensitive(config_dict)

    print("=" * 60)
    print("ChatrixCD Configuration")
    print("=" * 60)
    print(json.dumps(config_dict, indent=2))
    print("=" * 60)


def main():
    """Main entry point."""
    # Parse command-line arguments
    args = parse_args()

    # Handle --init flag first (before loading config)
    if args.init_config:
        from chatrixcd.config_wizard import (
            run_console_config_wizard,
            save_config,
        )

        print("\n" + "=" * 70)
        print("ChatrixCD Configuration Initialization")
        print("=" * 70)

        # Try to load existing config if it exists
        existing_config = None
        if os.path.exists(args.config):
            try:
                config_temp = Config(config_file=args.config)
                existing_config = config_temp.config
                print(f"\nFound existing configuration: {args.config}")
                print("Existing values will be used as defaults.\n")
            except Exception as e:
                print(f"\nWarning: Could not load existing config: {e}")
                print("Starting with default values.\n")
        else:
            print(f"\nNo existing configuration found at: {args.config}")
            print("Creating new configuration.\n")

        # Run the wizard
        new_config = run_console_config_wizard(existing_config)

        # Save the config
        if save_config(new_config, args.config):
            print("\n" + "=" * 70)
            print("Configuration complete!")
            print("=" * 70)
            print(
                f"\nYou can now start ChatrixCD with: chatrixcd -c {args.config}"
            )
            sys.exit(0)
        else:
            sys.exit(1)

    # Check if config file exists; if not, offer to create it
    if not os.path.exists(args.config):
        print(f"\nConfiguration file not found: {args.config}")
        print("\nWould you like to create it now?")
        print("  1. Yes, run configuration wizard")
        print("  2. No, use default values for this session")

        try:
            choice = input("\nEnter choice [1-2]: ").strip()
            if choice == "1":
                from chatrixcd.config_wizard import (
                    run_console_config_wizard,
                    save_config,
                )

                new_config = run_console_config_wizard(None)
                if save_config(new_config, args.config):
                    print("\nConfiguration saved! Starting ChatrixCD...\n")
                else:
                    print("\nFailed to save configuration. Exiting.")
                    sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\n\nUsing default values for this session.")

    # Load configuration first to get log file path
    config = Config(config_file=args.config)
    log_file = config.get("bot.log_file", "chatrixcd.log")

    # Get config values with command-line overrides
    # Verbosity: config verbosity is mapped to levels (silent=0, error=0, info=0, debug=1)
    config_verbosity = config.get("bot.verbosity", "info")
    verbosity_map = {"silent": 0, "error": 0, "info": 0, "debug": 1}
    config_verbosity_level = verbosity_map.get(config_verbosity, 0)
    verbosity = (
        args.verbosity if args.verbosity > 0 else config_verbosity_level
    )

    # Color: command-line -C flag overrides config
    color_enabled = args.color or config.get("bot.color_enabled", False)

    # Mouse: command-line -m flag overrides config
    mouse_enabled = args.mouse or config.get("bot.mouse_enabled", False)

    # Determine if we'll use TUI mode (before setting up logging)
    # TUI is used when:
    # - Not in daemon mode (-d)
    # - Not in log-only mode (-L)
    # - Running in an interactive terminal
    will_use_tui = not args.daemon and not args.log_only and sys.stdin.isatty()

    # Setup logging with verbosity, color, and redaction options
    # In TUI mode, only log to file (no console output) to avoid interference
    setup_logging(
        verbosity=verbosity,
        color=color_enabled,
        redact=args.redact,
        log_file=log_file,
        tui_mode=will_use_tui,
    )
    logger = logging.getLogger(__name__)

    # Daemonize if requested (Unix/Linux only)
    if args.daemon:
        if sys.platform == "win32":
            logger.error("Daemon mode is not supported on Windows")
            sys.exit(1)
        logger.info("Entering daemon mode...")
        daemonize()
        # Re-setup logging after daemonization
        # Daemon mode never uses TUI, so tui_mode=False
        setup_logging(
            verbosity=args.verbosity,
            color=False,
            redact=args.redact,
            log_file=log_file,
            tui_mode=False,
        )  # No color in daemon mode
        logger = logging.getLogger(__name__)

    logger.info(f"ChatrixCD {__version_full__} starting...")

    # Validate configuration before starting
    validation_errors = config.validate_schema()
    if validation_errors and not args.show_config:
        logger.error("Configuration validation failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        print("\nERROR: Configuration validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            f"\nPlease check your configuration file: {args.config}",
            file=sys.stderr,
        )
        print(
            "You can view your current configuration with: chatrixcd -s",
            file=sys.stderr,
        )
        sys.exit(1)

    # Apply command-line overrides
    if args.admin_users:
        bot_config = config.config.get("bot", {})
        existing_admins = bot_config.get("admin_users", [])
        # Merge and deduplicate
        all_admins = list(set(existing_admins + args.admin_users))
        config.config.setdefault("bot", {})["admin_users"] = all_admins
        logger.info(f"Admin users from command-line: {args.admin_users}")

    if args.allowed_rooms:
        bot_config = config.config.get("bot", {})
        existing_rooms = bot_config.get("allowed_rooms", [])
        # Merge and deduplicate
        all_rooms = list(set(existing_rooms + args.allowed_rooms))
        config.config.setdefault("bot", {})["allowed_rooms"] = all_rooms
        logger.info(f"Allowed rooms from command-line: {args.allowed_rooms}")

    if args.no_greetings:
        # Disable greetings if --no-greetings flag is set
        config.config.setdefault("bot", {})["greetings_enabled"] = False
        logger.info("Greetings disabled via --no-greetings flag")

    # Store redact flag in config for access by command handler
    if args.redact:
        config.config.setdefault("bot", {})["redact"] = True
        logger.info("Redaction enabled via --redact flag")

    # Show config and exit if requested
    if args.show_config:
        # Use TUI for show-config if not in redact mode and not verbose mode
        # Show config in console
        print_config(config, redact_identifiers=args.redact)
        sys.exit(0)

    # Determine operating mode
    # - daemon: Running in background with -D flag (auto-verify devices)
    # - log: Log-only mode with -L flag (interactive CLI verification)
    # - tui: Interactive TUI mode (default if terminal available)
    if args.daemon:
        mode = "daemon"
    elif args.log_only:
        mode = "log"
    else:
        mode = "tui" if sys.stdin.isatty() else "log"

    # Create bot with appropriate mode
    bot = ChatrixBot(config, mode=mode)

    # Determine if we should use TUI
    # Use TUI if:
    # - Not running in daemon mode (-D)
    # - Not in log-only mode (-L)
    # - Running in an interactive terminal
    use_tui = not args.daemon and not args.log_only and sys.stdin.isatty()

    # Get color theme from config
    color_theme = config.get("bot.color_theme", "default")

    try:
        if use_tui:
            # Run with TUI interface
            logger.info("Using TUI")
            asyncio.run(
                run_tui_with_bot(
                    bot,
                    config,
                    color_enabled,
                    mouse_enabled,
                    theme=color_theme,
                )
            )
        else:
            # Run in classic log-only mode
            asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        # Show stacktrace only in verbose mode (-v, -vv, -vvv)
        if args.verbosity >= 1:
            logger.error(f"Fatal error: {e}", exc_info=True)
        else:
            logger.error(f"Fatal error: {e}")
            print(f"\nError: {e}", file=sys.stderr)
            print("Run with -v or -vv for more details", file=sys.stderr)
        sys.exit(1)


async def run_tui_with_bot(
    bot, config, use_color: bool, mouse: bool = False, theme: str = "default"
):
    """Run the bot with TUI interface.

    This function starts the TUI first, then performs login within the TUI context.
    This is necessary because OIDC authentication may need to display screens in the TUI,
    and screens can only be pushed when the TUI is already running.

    Args:
        bot: The ChatrixBot instance
        config: Configuration object
        use_color: Whether to use colors
        mouse: Whether to enable mouse support (default: False)
        theme: Color theme to use ('default', 'midnight', 'grayscale', 'windows31', 'msdos')
    """
    import logging
    from nio import SyncResponse

    logger = logging.getLogger(__name__)

    # Import the TUI module
    from chatrixcd.tui.app import ChatrixTUI as TUIClass

    logger.info("Using modular TUI")

    # Create TUI app
    tui_app = TUIClass(bot, config, use_color=use_color, theme=theme)

    # Store reference to TUI app in bot for plugin access (e.g., OIDC plugin)
    bot.tui_app = tui_app

    # Set up login task that will be executed after TUI starts
    async def perform_login_and_sync():
        """Perform login and start sync loop after TUI is mounted."""
        logger.debug("Starting login process within TUI context")

        # Perform login (OIDC handled by plugin if enabled)
        login_success = await bot.login()

        if not login_success:
            logger.error("Failed to login, exiting TUI")
            tui_app.exit()
            return

        logger.info("Login successful, starting bot sync loop")

        # Send startup message
        await bot.send_startup_message()

        # Register sync callback
        bot.client.add_response_callback(bot.sync_callback, SyncResponse)

        # Start bot sync in background
        bot_task = asyncio.create_task(
            bot.client.sync_forever(timeout=30000, full_state=True)
        )

        # Store the task so we can cancel it later
        tui_app.bot_task = bot_task

    # Set the login task on the TUI app
    tui_app.login_task = perform_login_and_sync

    # Wrap login task with error handling
    async def perform_login_with_error_handling():
        """Wrap login in error handler to show user-friendly errors."""
        try:
            await perform_login_and_sync()
        except Exception as e:
            logger.error(
                f"Error during login/sync: {e}",
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            # Show error to user in TUI
            from chatrixcd.tui import MessageScreen

            error_msg = (
                f"[bold red]Error during login/sync:[/bold red]\n\n{str(e)}"
            )
            if not logger.isEnabledFor(logging.DEBUG):
                error_msg += (
                    "\n\n[dim]Run with -v or -vv for more details[/dim]"
                )
            tui_app.push_screen(MessageScreen(error_msg))

    # Override the login task with error-handling version
    tui_app.login_task = perform_login_with_error_handling

    # Run the TUI (login will happen in on_mount)
    try:
        await tui_app.run_async(mouse=mouse)
    except Exception as e:
        # Catch any unhandled TUI exceptions
        logger.error(
            f"TUI error: {e}", exc_info=logger.isEnabledFor(logging.DEBUG)
        )
        if logger.isEnabledFor(logging.DEBUG):
            # Only show stacktrace in debug mode (-v, -vv, -vvv)
            raise
        else:
            print(f"\nError: {e}", file=sys.stderr)
            print("Run with -v or -vv for more details", file=sys.stderr)
            sys.exit(1)
    finally:
        # Clean up
        if hasattr(tui_app, "bot_task") and tui_app.bot_task:
            tui_app.bot_task.cancel()
            try:
                await tui_app.bot_task
            except asyncio.CancelledError:
                pass
        await bot.close()


if __name__ == "__main__":
    main()
