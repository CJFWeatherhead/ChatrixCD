"""Shared file watching functionality for configuration files."""

import os
import logging
import asyncio
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches a file for changes and triggers reload callbacks."""

    def __init__(
        self,
        file_path: str,
        reload_callback: Callable[[], None],
        auto_reload: bool = False,
        check_interval: float = 5.0,
    ):
        """Initialize file watcher.

        Args:
            file_path: Path to file to watch
            reload_callback: Function to call when file changes
            auto_reload: If True, automatically start watching
            check_interval: How often to check for changes (seconds)
        """
        self.file_path = file_path
        self.reload_callback = reload_callback
        self.check_interval = check_interval
        self._last_mtime: Optional[float] = None
        self._reload_task: Optional[asyncio.Task] = None

        # Initialize last modified time if file exists
        if os.path.exists(file_path):
            self._last_mtime = os.path.getmtime(file_path)

        if auto_reload:
            self.start()

    def check_for_changes(self) -> bool:
        """Check if the watched file has been modified.

        Returns:
            True if file has been modified, False otherwise
        """
        if not os.path.exists(self.file_path):
            return False

        try:
            current_mtime = os.path.getmtime(self.file_path)
            if self._last_mtime is None or current_mtime > self._last_mtime:
                self._last_mtime = current_mtime
                return True
        except Exception as e:
            logger.warning(f"Failed to check file modification time for {self.file_path}: {e}")

        return False

    def start(self):
        """Start automatic file watching."""
        try:
            asyncio.get_running_loop()
            if self._reload_task is None or self._reload_task.done():
                self._reload_task = asyncio.create_task(self._watch_loop())
                logger.info(f"Started file watcher for {self.file_path}")
        except RuntimeError:
            logger.debug(
                f"No event loop available yet, file watcher for {self.file_path} will start when bot runs"
            )

    def stop(self):
        """Stop automatic file watching."""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            logger.info(f"Stopped file watcher for {self.file_path}")

    async def _watch_loop(self):
        """Background task that checks for file changes and triggers reload."""
        try:
            while True:
                await asyncio.sleep(self.check_interval)

                if self.check_for_changes():
                    logger.info(f"File {self.file_path} has been modified, reloading...")
                    try:
                        self.reload_callback()
                    except Exception as e:
                        logger.error(f"Error in reload callback for {self.file_path}: {e}")

        except asyncio.CancelledError:
            logger.debug(f"File watcher task cancelled for {self.file_path}")
        except Exception as e:
            logger.error(f"Error in file watch loop for {self.file_path}: {e}")
