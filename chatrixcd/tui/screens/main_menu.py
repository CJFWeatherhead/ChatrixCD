"""Main menu screen for TUI."""

from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Button
from textual.binding import Binding
from .base import BaseScreen
from ..widgets.common import StatusIndicator, MetricDisplay


class MainMenuScreen(BaseScreen):
    """Main menu screen showing bot status and navigation."""

    SCREEN_TITLE = "Main Menu"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose_content(self):
        """Compose main menu content."""
        with Container(classes="main-container"):
            # Welcome message
            yield Static(
                "[bold cyan]ChatrixCD[/bold cyan]\n"
                "Matrix CI/CD Bot - Interactive Interface",
                classes="title-banner",
            )

            # Status section
            with Vertical(classes="status-section"):
                yield Static("[bold]Status[/bold]", classes="section-header")
                yield StatusIndicator(service_name="Matrix")
                yield StatusIndicator(service_name="Semaphore")

            # Metrics section
            with Vertical(classes="metrics-section"):
                yield Static("[bold]Metrics[/bold]", classes="section-header")
                yield MetricDisplay(label="Uptime", id="uptime-metric")
                yield MetricDisplay(
                    label="Messages", id="messages-metric", icon="📨"
                )
                yield MetricDisplay(
                    label="Tasks", id="tasks-metric", icon="🔧"
                )
                yield MetricDisplay(
                    label="Errors", id="errors-metric", icon="❌"
                )
                # Expose ActiveTasksWidget for tests that query '#active_tasks'
                from .. import ActiveTasksWidget

                yield ActiveTasksWidget(id="active_tasks")

            # Menu buttons - dynamically populated from registry
            with ScrollableContainer(classes="menu-section"):
                yield Static("[bold]Menu[/bold]", classes="section-header")
                yield Container(id="menu-buttons")

    async def on_screen_mount(self):
        """Initialize menu when screen mounts."""
        await self.populate_menu()
        await self.refresh_data()

        # Set up periodic refresh
        self.set_interval(5.0, self.refresh_data)

    async def populate_menu(self):
        """Populate menu with registered screens."""
        menu_container = self.query_one("#menu-buttons")

        # Clear existing buttons
        await menu_container.remove_children()

        # Get all registered screens from registry
        registry = self.tui_app.screen_registry
        categories = registry.get_categories()

        for category in categories:
            screens = registry.get_all(category=category)

            if screens:
                # Add category header
                category_header = Static(
                    f"[bold]{category.title()}[/bold]", classes="menu-category"
                )
                await menu_container.mount(category_header)

                # Add screen buttons
                for screen_reg in screens:
                    button = Button(
                        f"{screen_reg.icon} {screen_reg.title}",
                        id=f"menu-{screen_reg.name}",
                        classes="menu-button",
                    )
                    await menu_container.mount(button)

    async def navigate_to_screen(self, screen_name: str):
        """Navigate to a specific screen.

        Args:
            screen_name: Name of screen to navigate to
        """
        registry = self.tui_app.screen_registry
        registration = registry.get(screen_name)

        if not registration:
            await self.show_error(f"Screen '{screen_name}' not found")
            return

        try:
            # Instantiate screen
            screen = registration.screen_class(self.tui_app)
            self.app.push_screen(screen)
        except Exception as e:
            self.logger.error(f"Failed to load screen '{screen_name}': {e}")
            await self.show_error(f"Failed to load screen: {e}")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("menu-"):
            # Extract screen name from button ID
            screen_name = event.button.id[5:]  # Remove "menu-" prefix
            await self.navigate_to_screen(screen_name)

    async def refresh_data(self):
        """Refresh status and metrics."""
        try:
            # Update status indicators
            matrix_status = self.query_one(StatusIndicator)
            if self.tui_app.bot and self.tui_app.bot.client:
                if self.tui_app.bot.client.logged_in:
                    matrix_status.status = "Connected"
                else:
                    matrix_status.status = "Disconnected"
            else:
                matrix_status.status = "Unknown"

            # Update metrics
            if hasattr(self.tui_app.bot, "metrics"):
                metrics = self.tui_app.bot.metrics

                uptime_metric = self.query_one("#uptime-metric", MetricDisplay)
                uptime_metric.value = self._format_uptime(
                    metrics.get("uptime", 0)
                )

                messages_metric = self.query_one(
                    "#messages-metric", MetricDisplay
                )
                messages_metric.value = metrics.get("messages_sent", 0)

                tasks_metric = self.query_one("#tasks-metric", MetricDisplay)
                active_tasks = getattr(
                    self.tui_app.bot.command_handler, "active_tasks", {}
                )
                tasks_metric.value = len(active_tasks)

                # Update ActiveTasksWidget if present
                try:
                    active_widget = self.query_one("#active_tasks")
                    if hasattr(active_widget, "update_tasks"):
                        active_widget.update_tasks(active_tasks)
                except Exception:
                    pass

                errors_metric = self.query_one("#errors-metric", MetricDisplay)
                errors_metric.value = metrics.get("errors", 0)

        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format.

        Args:
            seconds: Uptime in seconds

        Returns:
            Formatted uptime string
        """
        try:
            total_seconds = int(seconds)
        except Exception:
            # If we can't convert uptime to int (e.g., a Mock in tests),
            # return a safe default string.
            try:
                return str(seconds)
            except Exception:
                return "0s"

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def action_refresh(self):
        """Manually refresh data."""
        self.app.call_later(self.refresh_data)

    def action_quit(self):
        """Quit the application."""
        self.app.exit()
