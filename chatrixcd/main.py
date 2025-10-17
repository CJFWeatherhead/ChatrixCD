"""Main entry point for ChatrixCD bot."""

import argparse
import asyncio
import logging
import os
import sys
from chatrixcd import __version__
from chatrixcd.config import Config
from chatrixcd.bot import ChatrixBot
from chatrixcd.redactor import SensitiveInfoRedactor, RedactingFilter


def setup_logging(verbosity: int = 0, color: bool = False, redact: bool = False, log_file: str = 'chatrixcd.log', tui_mode: bool = False):
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
            handler.setFormatter(colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            ))
            handlers = [handler, logging.FileHandler(log_file)]
        except ImportError:
            # Fallback if colorlog not available
            handlers = [
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file)
            ]
    else:
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Add redaction filter if requested
    if redact:
        redactor = SensitiveInfoRedactor(enabled=True, colorize=color)
        redacting_filter = RedactingFilter(redactor)
        for handler in logging.root.handlers:
            handler.addFilter(redacting_filter)
    
    # Set even more verbose logging for key modules if verbosity >= 2
    if verbosity >= 2:
        logging.getLogger('nio').setLevel(logging.DEBUG)
        logging.getLogger('aiohttp').setLevel(logging.DEBUG)


def parse_args():
    """Parse command-line arguments.
    
    Returns:
        Namespace object containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='chatrixcd',
        description='ChatrixCD - Matrix bot for CI/CD automation with Semaphore UI',
        epilog='For more information, visit: https://github.com/CJFWeatherhead/ChatrixCD'
    )
    
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'ChatrixCD {__version__}'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        dest='verbosity',
        help='Increase verbosity (-v for DEBUG, -vv for detailed DEBUG with library logs)'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.json',
        metavar='FILE',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '-C', '--color',
        action='store_true',
        help='Enable colored logging output (requires colorlog package)'
    )
    
    parser.add_argument(
        '-D', '--daemon',
        action='store_true',
        help='Run in daemon mode (detach from terminal and run in background)'
    )
    
    parser.add_argument(
        '-s', '--show-config',
        action='store_true',
        dest='show_config',
        help='Display configuration and exit (credentials will be redacted)'
    )
    
    parser.add_argument(
        '-a', '--admin',
        action='append',
        dest='admin_users',
        metavar='USER',
        help='Add admin user (can be specified multiple times, e.g., -a @user1:matrix.org -a @user2:matrix.org)'
    )
    
    parser.add_argument(
        '-r', '--room',
        action='append',
        dest='allowed_rooms',
        metavar='ROOM',
        help='Add allowed room (can be specified multiple times, e.g., -r !room1:matrix.org -r !room2:matrix.org)'
    )
    
    parser.add_argument(
        '-R', '--redact',
        action='store_true',
        help='Redact sensitive information from logs (room names, usernames, IPs, tokens, etc.)'
    )
    
    parser.add_argument(
        '-L', '--log-only',
        action='store_true',
        dest='log_only',
        help='Run in classic log-only mode (no TUI, only show logs)'
    )
    
    return parser.parse_args()


def daemonize():
    """Daemonize the process (Unix/Linux only).
    
    Forks the process into the background and detaches from the terminal.
    """
    try:
        pid = os.fork()
        if pid > 0:
            # Exit parent process
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #1 failed: {e}\n")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
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
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(os.devnull, 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(os.devnull, 'a+') as f:
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
    sensitive_fields = ['password', 'access_token', 'api_token', 'client_secret', 'oidc_client_secret']
    
    # Additional fields to redact when redact_identifiers is enabled
    identifier_fields = ['user_id', 'homeserver', 'url', 'admin_users', 'allowed_rooms']
    
    def redact_sensitive(obj, path=''):
        """Recursively redact sensitive fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in sensitive_fields and value:
                    obj[key] = '***REDACTED***'
                elif redact_identifiers and key in identifier_fields and value:
                    if isinstance(value, str):
                        # Use redactor for proper redaction
                        redactor = SensitiveInfoRedactor(enabled=True, colorize=False)
                        obj[key] = redactor.redact(value)
                    elif isinstance(value, list):
                        redactor = SensitiveInfoRedactor(enabled=True, colorize=False)
                        obj[key] = [redactor.redact(str(v)) for v in value]
                else:
                    redact_sensitive(value, f'{path}.{key}' if path else key)
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
    
    # Load configuration first to get log file path
    config = Config(config_file=args.config)
    log_file = config.get('bot.log_file', 'chatrixcd.log')
    
    # Determine if we'll use TUI mode (before setting up logging)
    # TUI is used when:
    # - Not in daemon mode (-d)
    # - Not in log-only mode (-L)
    # - Running in an interactive terminal
    will_use_tui = not args.daemon and not args.log_only and sys.stdin.isatty()
    
    # Setup logging with verbosity, color, and redaction options
    # In TUI mode, only log to file (no console output) to avoid interference
    setup_logging(
        verbosity=args.verbosity, 
        color=args.color, 
        redact=args.redact, 
        log_file=log_file,
        tui_mode=will_use_tui
    )
    logger = logging.getLogger(__name__)
    
    # Daemonize if requested (Unix/Linux only)
    if args.daemon:
        if sys.platform == 'win32':
            logger.error("Daemon mode is not supported on Windows")
            sys.exit(1)
        logger.info("Entering daemon mode...")
        daemonize()
        # Re-setup logging after daemonization
        # Daemon mode never uses TUI, so tui_mode=False
        setup_logging(verbosity=args.verbosity, color=False, redact=args.redact, log_file=log_file, tui_mode=False)  # No color in daemon mode
        logger = logging.getLogger(__name__)
    
    logger.info(f"ChatrixCD {__version__} starting...")
    
    # Validate configuration before starting
    validation_errors = config.validate_schema()
    if validation_errors and not args.show_config:
        logger.error("Configuration validation failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        print("\nERROR: Configuration validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
        print(f"\nPlease check your configuration file: {args.config}", file=sys.stderr)
        print("You can view your current configuration with: chatrixcd -s", file=sys.stderr)
        sys.exit(1)
    
    # Apply command-line overrides
    if args.admin_users:
        bot_config = config.config.get('bot', {})
        existing_admins = bot_config.get('admin_users', [])
        # Merge and deduplicate
        all_admins = list(set(existing_admins + args.admin_users))
        config.config.setdefault('bot', {})['admin_users'] = all_admins
        logger.info(f"Admin users from command-line: {args.admin_users}")
    
    if args.allowed_rooms:
        bot_config = config.config.get('bot', {})
        existing_rooms = bot_config.get('allowed_rooms', [])
        # Merge and deduplicate
        all_rooms = list(set(existing_rooms + args.allowed_rooms))
        config.config.setdefault('bot', {})['allowed_rooms'] = all_rooms
        logger.info(f"Allowed rooms from command-line: {args.allowed_rooms}")
    
    # Show config and exit if requested
    if args.show_config:
        # Use TUI for show-config if not in redact mode and not verbose mode
        use_tui_for_config = not args.redact and args.verbosity == 0 and sys.stdin.isatty()
        
        if use_tui_for_config:
            # Show config in TUI window
            from chatrixcd.tui import show_config_tui
            try:
                asyncio.run(show_config_tui(config))
            except KeyboardInterrupt:
                pass
        else:
            # Show config in console (original behavior)
            print_config(config, redact_identifiers=args.redact)
        sys.exit(0)
    
    # Create and run bot
    bot = ChatrixBot(config)
    
    # Determine if we should use TUI
    # Use TUI if:
    # - Not running in daemon mode (-D)
    # - Not in log-only mode (-L)
    # - Running in an interactive terminal
    use_tui = not args.daemon and not args.log_only and sys.stdin.isatty()
    
    try:
        if use_tui:
            # Run with TUI interface
            from chatrixcd.tui import run_tui
            asyncio.run(run_tui_with_bot(bot, config, args.color))
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


async def run_tui_with_bot(bot, config, use_color: bool):
    """Run the bot with TUI interface.
    
    This function starts the TUI first, then performs login within the TUI context.
    This is necessary because OIDC authentication may need to display screens in the TUI,
    and screens can only be pushed when the TUI is already running.
    
    Args:
        bot: The ChatrixBot instance
        config: Configuration object
        use_color: Whether to use colors
    """
    import logging
    from chatrixcd.tui import ChatrixTUI, OIDCAuthScreen
    from nio import SyncResponse
    
    logger = logging.getLogger(__name__)
    
    # Create TUI app
    tui_app = ChatrixTUI(bot, config, use_color=use_color)
    
    # Create OIDC callback that uses the TUI
    async def oidc_token_callback(sso_url: str, redirect_url: str, identity_providers: list) -> str:
        """TUI-based OIDC token input.
        
        Args:
            sso_url: SSO authentication URL
            redirect_url: Redirect URL for callback
            identity_providers: List of available identity providers
            
        Returns:
            Login token from user
        """
        logger.debug("OIDC callback invoked, pushing OIDC auth screen to TUI")
        
        # Create a future to receive the token
        token_future = asyncio.Future()
        
        def handle_result(token):
            logger.debug(f"OIDC screen dismissed with token: {'<provided>' if token else '<cancelled>'}")
            if token:
                token_future.set_result(token)
            else:
                token_future.set_exception(Exception("OIDC authentication cancelled"))
        
        # Show OIDC screen (TUI must be running for this to work)
        tui_app.push_screen(OIDCAuthScreen(sso_url, redirect_url, identity_providers), handle_result)
        
        # Wait for user to submit token
        token = await token_future
        return token
    
    # Set up login task that will be executed after TUI starts
    async def perform_login_and_sync():
        """Perform login and start sync loop after TUI is mounted."""
        logger.debug("Starting login process within TUI context")
        
        # Perform login with TUI callback for OIDC
        login_success = await bot.login(oidc_token_callback=oidc_token_callback)
        
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
        bot_task = asyncio.create_task(bot.client.sync_forever(timeout=30000, full_state=True))
        
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
            logger.error(f"Error during login/sync: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
            # Show error to user in TUI
            from chatrixcd.tui import MessageScreen
            error_msg = f"[bold red]Error during login/sync:[/bold red]\n\n{str(e)}"
            if not logger.isEnabledFor(logging.DEBUG):
                error_msg += "\n\n[dim]Run with -v or -vv for more details[/dim]"
            tui_app.push_screen(MessageScreen(error_msg))
    
    # Override the login task with error-handling version
    tui_app.login_task = perform_login_with_error_handling
    
    # Run the TUI (login will happen in on_mount)
    try:
        await tui_app.run_async()
    except Exception as e:
        # Catch any unhandled TUI exceptions
        logger.error(f"TUI error: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        if logger.isEnabledFor(logging.DEBUG):
            # Only show stacktrace in debug mode (-v, -vv, -vvv)
            raise
        else:
            print(f"\nError: {e}", file=sys.stderr)
            print("Run with -v or -vv for more details", file=sys.stderr)
            sys.exit(1)
    finally:
        # Clean up
        if hasattr(tui_app, 'bot_task') and tui_app.bot_task:
            tui_app.bot_task.cancel()
            try:
                await tui_app.bot_task
            except asyncio.CancelledError:
                pass
        await bot.close()


if __name__ == "__main__":
    main()
