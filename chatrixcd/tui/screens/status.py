"""Status screen showing detailed bot status."""

from textual.containers import Container, Grid, Vertical
from textual.widgets import Static

from ..widgets.common import MetricDisplay, StatusIndicator
from .base import BaseScreen


class StatusScreen(BaseScreen):
    """Screen showing detailed bot status and metrics."""

    SCREEN_TITLE = "Bot Status"

    CSS = """
    .status-container {
        width: 100%;
        height: 100%;
        layout: vertical;
    }

    .status-grid {
        grid-size: 2;
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    .status-grid > * {
        height: auto;
        width: 100%;
    }

    /* Stack status indicators vertically on small screens */
    .compact .status-grid {
        grid-size: 1;
    }

    .metrics-container {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    .metrics-container > * {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    .plugins-list {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    .tasks-list {
        width: 100%;
        height: auto;
    }

    .section-header {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }
    """

    def compose_content(self):
        """Compose status screen content."""
        with Container(classes="status-container"):
            yield Static("[bold cyan]Bot Status[/bold cyan]", classes="section-header")

            # Connection status
            with Grid(classes="status-grid"):
                yield StatusIndicator(service_name="Matrix", id="matrix-status")
                yield StatusIndicator(service_name="Semaphore", id="semaphore-status")
                yield StatusIndicator(service_name="Encryption", id="encryption-status")

            yield Static("[bold cyan]Metrics[/bold cyan]", classes="section-header")

            # Metrics display
            with Vertical(classes="metrics-container"):
                yield MetricDisplay(label="Uptime", id="uptime", icon="⏱️")
                yield MetricDisplay(
                    label="Messages Sent", id="messages_sent", icon="📨"
                )
                yield MetricDisplay(
                    label="Requests Received",
                    id="requests_received",
                    icon="📥",
                )
                yield MetricDisplay(label="Active Tasks", id="active_tasks", icon="🔧")
                yield MetricDisplay(label="Errors", id="errors", icon="❌")
                yield MetricDisplay(label="Emojis Used", id="emojis_used", icon="😊")

            # Plugins section
            yield Static(
                "[bold cyan]Loaded Plugins[/bold cyan]", classes="section-header"
            )
            yield Static(id="plugins-list", classes="plugins-list")

            # Active tasks section
            yield Static(
                "[bold cyan]Active Tasks[/bold cyan]", classes="section-header"
            )
            yield Static(id="active-tasks-list", classes="tasks-list")

    async def on_screen_mount(self):
        """Set up periodic refresh."""
        await self.refresh_data()
        self.set_interval(3.0, self.refresh_data)

    async def refresh_data(self):
        """Refresh status and metrics data."""
        try:
            # Update Matrix status
            matrix_status = self.query_one("#matrix-status", StatusIndicator)
            if self.tui_app.bot and self.tui_app.bot.client:
                if self.tui_app.bot.client.logged_in:
                    matrix_status.status = "Connected"
                else:
                    matrix_status.status = "Disconnected"
            else:
                matrix_status.status = "Unknown"

            # Update Semaphore status
            semaphore_status = self.query_one("#semaphore-status", StatusIndicator)
            if self.tui_app.bot and self.tui_app.bot.semaphore:
                # Simple check - could be enhanced with actual health check
                semaphore_status.status = "Connected"
            else:
                semaphore_status.status = "Unknown"

            # Update Encryption status
            encryption_status = self.query_one("#encryption-status", StatusIndicator)
            if self.tui_app.bot and self.tui_app.bot.client:
                if self.tui_app.bot.client.olm:
                    # Check if we have any verified devices
                    try:
                        from ...verification import DeviceVerificationManager

                        verification_manager = DeviceVerificationManager(
                            self.tui_app.bot.client
                        )
                        verified_devices = (
                            await verification_manager.get_verified_devices()
                        )
                        if verified_devices:
                            encryption_status.status = (
                                f"E2E ({len(verified_devices)} verified)"
                            )
                        else:
                            encryption_status.status = "E2E (unverified)"
                    except Exception:
                        encryption_status.status = "E2E (unknown)"
                else:
                    encryption_status.status = "Disabled"
            else:
                encryption_status.status = "Unknown"

            # Update metrics
            if hasattr(self.tui_app.bot, "metrics"):
                metrics = self.tui_app.bot.metrics

                self.query_one("#uptime", MetricDisplay).value = self._format_uptime(
                    metrics.get("uptime", 0)
                )
                self.query_one("#messages_sent", MetricDisplay).value = metrics.get(
                    "messages_sent", 0
                )
                self.query_one("#requests_received", MetricDisplay).value = metrics.get(
                    "requests_received", 0
                )
                self.query_one("#errors", MetricDisplay).value = metrics.get(
                    "errors", 0
                )
                self.query_one("#emojis_used", MetricDisplay).value = metrics.get(
                    "emojis_used", 0
                )

            # Update active tasks
            if hasattr(self.tui_app.bot, "command_handler"):
                active_tasks = getattr(
                    self.tui_app.bot.command_handler, "active_tasks", {}
                )
                self.query_one("#active_tasks", MetricDisplay).value = len(active_tasks)

                # Format active tasks list
                tasks_widget = self.query_one("#active-tasks-list", Static)
                if active_tasks:
                    tasks_text = []
                    for task_id, task_info in active_tasks.items():
                        status = task_info.get("status", "unknown")
                        project_id = task_info.get("project_id", "?")

                        # Color code by status
                        color = {
                            "running": "yellow",
                            "success": "green",
                            "error": "red",
                            "stopping": "orange",
                        }.get(status, "white")

                        icon = {
                            "running": "🔄",
                            "success": "✅",
                            "error": "❌",
                            "stopping": "⏸️",
                        }.get(status, "•")

                        tasks_text.append(
                            f"[{color}]{icon} Task {task_id}[/{color}] "
                            f"(Project {project_id}): {status}"
                        )
                    tasks_widget.update("\n".join(tasks_text))
                else:
                    tasks_widget.update("[dim]No active tasks[/dim]")

                # Update plugins list
                plugins_widget = self.query_one("#plugins-list", Static)
                if hasattr(self.tui_app.bot, "plugin_manager"):
                    plugin_manager = self.tui_app.bot.plugin_manager
                    plugins_status = plugin_manager.get_all_plugins_status()

                    if plugins_status:
                        plugins_text = []
                        for status in plugins_status:
                            name = status.get("name", "Unknown")
                            version = status.get("version", "0.0.0")
                            plugin_type = status.get("type", "generic")
                            description = status.get("description", "")
                            enabled = status.get("enabled", False)

                            # Color and icon based on enabled status
                            if enabled:
                                color = "green"
                                icon = "✅"
                            else:
                                color = "red"
                                icon = "❌"

                            plugin_line = f"[{color}]{icon} {name} v{version}[/{color}] ({plugin_type})"
                            if description:
                                plugin_line += f" - {description}"
                            plugins_text.append(plugin_line)

                        plugins_widget.update("\n".join(plugins_text))
                    else:
                        plugins_widget.update("[dim]No plugins loaded[/dim]")
                else:
                    plugins_widget.update("[dim]Plugin manager not available[/dim]")

        except Exception as e:
            self.logger.error(f"Error refreshing status: {e}")

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        try:
            total = int(seconds)
        except Exception:
            try:
                return str(seconds)
            except Exception:
                total = 0

        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
