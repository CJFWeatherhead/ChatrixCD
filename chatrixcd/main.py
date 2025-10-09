"""Main entry point for ChatrixCD bot."""

import argparse
import asyncio
import logging
import os
import sys
from chatrixcd import __version__
from chatrixcd.config import Config
from chatrixcd.bot import ChatrixBot


def setup_logging(verbosity: int = 0, color: bool = False):
    """Setup logging configuration.
    
    Args:
        verbosity: Verbosity level (0=INFO, 1=DEBUG, 2+=detailed DEBUG)
        color: Enable colored logging output
    """
    # Determine log level based on verbosity
    if verbosity == 0:
        level = logging.INFO
    elif verbosity == 1:
        level = logging.DEBUG
    else:
        level = logging.DEBUG
    
    # Setup format with optional color support
    if color:
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
            handlers = [handler, logging.FileHandler('chatrixcd.log')]
        except ImportError:
            # Fallback if colorlog not available
            handlers = [
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('chatrixcd.log')
            ]
    else:
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('chatrixcd.log')
        ]
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
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


def print_config(config: Config):
    """Print configuration with redacted credentials.
    
    Args:
        config: Configuration object to print
    """
    import json
    import copy
    
    # Deep copy config to avoid modifying original
    config_dict = copy.deepcopy(config.config)
    
    # Redact sensitive fields
    sensitive_fields = ['password', 'access_token', 'api_token', 'client_secret', 'oidc_client_secret']
    
    def redact_sensitive(obj, path=''):
        """Recursively redact sensitive fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in sensitive_fields and value:
                    obj[key] = '***REDACTED***'
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
    
    # Setup logging with verbosity and color options
    setup_logging(verbosity=args.verbosity, color=args.color)
    logger = logging.getLogger(__name__)
    
    # Daemonize if requested (Unix/Linux only)
    if args.daemon:
        if sys.platform == 'win32':
            logger.error("Daemon mode is not supported on Windows")
            sys.exit(1)
        logger.info("Entering daemon mode...")
        daemonize()
        # Re-setup logging after daemonization
        setup_logging(verbosity=args.verbosity, color=False)  # No color in daemon mode
        logger = logging.getLogger(__name__)
    
    logger.info(f"ChatrixCD {__version__} starting...")
    
    # Load configuration with CLI overrides
    config = Config(config_file=args.config)
    
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
        print_config(config)
        sys.exit(0)
    
    # Create and run bot
    bot = ChatrixBot(config)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
