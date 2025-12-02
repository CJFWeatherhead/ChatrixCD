"""Logs screen showing bot logs."""

import os

from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static, TextArea

from .base import BaseScreen


class LogsScreen(BaseScreen):
    """Screen for viewing bot logs."""

    SCREEN_TITLE = "Logs"

    CSS = """
    .logs-container {
        height: auto;
    }

    .log-viewer {
        height: auto;
        max-height: 20;
        min-height: 10;
    }

    /* Responsive log viewer sizing */
    .compact .log-viewer {
        max-height: 12;
        min-height: 8;
    }
    """

    BINDINGS = [
        Binding("escape", "go_back", "Back", priority=True),
        Binding("b", "go_back", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose_content(self):
        """Compose logs screen content."""
        with Container(classes="logs-container"):
            yield Static("[bold cyan]Bot Logs[/bold cyan]", classes="section-header")
            yield Static("Last 1000 lines (most recent first):", classes="description")

            yield TextArea(
                id="log-content",
                read_only=True,
                show_line_numbers=False,
                classes="log-viewer",
            )

    async def on_screen_mount(self):
        """Load logs when screen mounts."""
        await self.refresh_data()

    async def refresh_data(self):
        """Refresh log content."""
        try:
            log_content = self._load_logs()
            text_area = self.query_one("#log-content", TextArea)
            await text_area.load_text(log_content)

        except Exception as e:
            self.logger.error(f"Error loading logs: {e}")
            await self.show_error(f"Failed to load logs: {e}")

    def _load_logs(self, max_lines: int = 1000) -> str:
        """Load log file content.

        Args:
            max_lines: Maximum number of lines to load

        Returns:
            Log content as string
        """
        try:
            # Get log file path from config
            bot_config = self.tui_app.config.get_bot_config()
            log_file = bot_config.get("log_file", "chatrixcd.log")

            if not os.path.exists(log_file):
                return f"[dim]Log file not found: {log_file}[/dim]"

            # Read last N lines
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Get last max_lines, reverse so newest is first
            recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
            recent_lines.reverse()

            return "".join(recent_lines)

        except Exception as e:
            self.logger.error(f"Error loading log file: {e}")
            return f"[red]Error loading logs: {e}[/red]"

    def action_refresh(self):
        """Manually refresh logs."""
        self.app.call_later(self.refresh_data)
