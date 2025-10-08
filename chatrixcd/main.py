"""Main entry point for ChatrixCD bot."""

import asyncio
import logging
import sys
from chatrixcd.config import Config
from chatrixcd.bot import ChatrixBot


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('chatrixcd.log')
        ]
    )


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("ChatrixCD starting...")
    
    # Load configuration
    config = Config()
    
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
