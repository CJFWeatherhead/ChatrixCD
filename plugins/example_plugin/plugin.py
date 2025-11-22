"""Example Plugin - Demonstrates the ChatrixCD plugin API."""

import asyncio
import logging
from typing import Dict, Any
from chatrixcd.plugin_manager import Plugin

logger = logging.getLogger(__name__)


class ExamplePlugin(Plugin):
    """Example plugin demonstrating the plugin API.

    This plugin can be used as a template for creating new plugins.
    It shows how to:
    - Implement the plugin interface
    - Access bot functionality
    - Use configuration
    - Log information
    - Run background tasks
    """

    def __init__(self, bot: Any, config: Dict[str, Any], metadata: Any):
        """Initialize the example plugin.

        Args:
            bot: Reference to ChatrixBot instance
            config: Plugin configuration
            metadata: Plugin metadata
        """
        super().__init__(bot, config, metadata)

        # Plugin-specific configuration
        self.example_setting = config.get("example_setting", "default_value")
        self.another_setting = config.get("another_setting", 42)

        # Plugin state
        self.is_running = False
        self.background_task: asyncio.Task = None
        self.message_count = 0

    async def initialize(self) -> bool:
        """Initialize the plugin.

        This is called when the plugin is loaded. Perform any necessary
        setup here (e.g., validate configuration, connect to services).

        Returns:
            True if initialization was successful, False otherwise
        """
        self.logger.info(
            f"Initializing Example Plugin v{self.metadata.version}"
        )
        self.logger.info(f"Example setting: {self.example_setting}")
        self.logger.info(f"Another setting: {self.another_setting}")

        # Validate configuration
        if not isinstance(self.another_setting, int):
            self.logger.error("'another_setting' must be an integer")
            return False

        # You can access bot components here
        if hasattr(self.bot, "semaphore"):
            self.logger.debug("Semaphore client is available")

        if hasattr(self.bot, "client"):
            self.logger.debug("Matrix client is available")

        self.logger.info("Example Plugin initialized successfully")
        return True

    async def start(self) -> bool:
        """Start the plugin.

        This is called to start the plugin's main functionality.
        Start background tasks, connect to services, etc.

        Returns:
            True if started successfully, False otherwise
        """
        self.logger.info("Starting Example Plugin")
        self.is_running = True

        # Start a background task
        self.background_task = asyncio.create_task(self._background_loop())

        self.logger.info("Example Plugin started successfully")
        return True

    async def stop(self):
        """Stop the plugin.

        This is called to stop the plugin's functionality cleanly.
        Stop background tasks, close connections, etc.
        """
        self.logger.info("Stopping Example Plugin")
        self.is_running = False

        # Stop background task
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Example Plugin stopped")

    async def cleanup(self):
        """Clean up resources.

        This is called when the plugin is being unloaded.
        Free resources, close file handles, etc.
        """
        self.logger.info("Cleaning up Example Plugin")

        # Ensure background task is stopped
        await self.stop()

        self.logger.info("Example Plugin cleaned up")

    async def _background_loop(self):
        """Background task that runs periodically.

        This demonstrates how to run a background task in your plugin.
        """
        self.logger.info("Background task started")

        try:
            while self.is_running:
                # Do some periodic work
                await asyncio.sleep(60)  # Run every 60 seconds

                self.logger.debug("Background task tick")
                self.message_count += 1

                # Example: You could check for events, update status, etc.

        except asyncio.CancelledError:
            self.logger.info(
                "Background task cancelled during plugin stop (expected)"
            )
            raise
        except Exception as e:
            self.logger.error(f"Background task error: {e}", exc_info=True)
        finally:
            self.logger.info("Background task stopped")

    async def send_example_notification(self, room_id: str):
        """Example method showing how to send messages.

        This demonstrates how to interact with Matrix from your plugin.

        Args:
            room_id: Matrix room ID to send message to
        """
        try:
            # Plain text message
            plain_text = (
                f"Hello from Example Plugin! (message #{self.message_count})"
            )

            # HTML formatted message
            html_text = f"<b>Hello from Example Plugin!</b> (message <code>#{self.message_count}</code>)"

            # Send message using bot
            event_id = await self.bot.send_message(
                room_id, plain_text, html_text
            )

            # Optionally send a reaction
            if event_id:
                await self.bot.send_reaction(room_id, event_id, "🎉")

            self.logger.info(f"Sent notification to {room_id}")

        except Exception as e:
            self.logger.error(
                f"Failed to send notification: {e}", exc_info=True
            )

    async def check_semaphore_connection(self) -> bool:
        """Example method showing how to use Semaphore client.

        This demonstrates how to interact with Semaphore from your plugin.

        Returns:
            True if Semaphore is accessible, False otherwise
        """
        try:
            # Use the bot's Semaphore client
            success = await self.bot.semaphore.ping()

            if success:
                self.logger.info("Semaphore server is accessible")

                # You can also get server info
                info = await self.bot.semaphore.get_info()
                if info:
                    self.logger.info(
                        f"Semaphore version: {info.get('version', 'unknown')}"
                    )
            else:
                self.logger.warning("Semaphore server is not accessible")

            return success

        except Exception as e:
            self.logger.error(f"Error checking Semaphore: {e}", exc_info=True)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information.

        This is called by the plugin manager to get current status.
        Include any useful information about your plugin's state.

        Returns:
            Dictionary with status information
        """
        status = super().get_status()

        # Add plugin-specific status
        status["is_running"] = self.is_running
        status["message_count"] = self.message_count
        status["example_setting"] = self.example_setting
        status["another_setting"] = self.another_setting
        status["background_task_active"] = (
            self.background_task is not None
            and not self.background_task.done()
        )

        return status


# Additional classes can be defined here if needed
# But only classes inheriting from Plugin will be loaded


class ExampleHelper:
    """Example helper class (not loaded as a plugin).

    You can define additional classes in your plugin.py that are not
    plugins themselves but are used by your plugin.
    """

    @staticmethod
    def format_message(text: str) -> str:
        """Format a message with plugin branding.

        Args:
            text: Message text

        Returns:
            Formatted message
        """
        return f"[Example Plugin] {text}"
