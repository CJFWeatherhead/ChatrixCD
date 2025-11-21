"""Base screen class for TUI."""

import logging
from typing import Optional, Any
from textual.screen import Screen
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Header, Footer

logger = logging.getLogger(__name__)


class BaseScreen(Screen):
    """Base class for all TUI screens.

    Provides common functionality like header/footer, navigation,
    and data refresh hooks.
    """

    # Default key bindings for all screens
    BINDINGS = [
        Binding("escape", "go_back", "Back", priority=True),
        Binding("b", "go_back", "Back"),
    ]

    # Screen metadata
    SCREEN_TITLE = "Screen"
    SHOW_HEADER = True
    SHOW_FOOTER = True

    def __init__(
        self,
        tui_app: Optional[Any] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        """Initialize base screen.

        Args:
            tui_app: Reference to main TUI application
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        # Allow screens to be instantiated outside of a running App for tests
        # by making tui_app optional. When mounted by Textual, Screen.app
        # will be set automatically by the framework.
        self.tui_app = tui_app
        # Construct a concise logger name for the screen
        screen_title = self.SCREEN_TITLE.lower()
        screen_key = screen_title.replace(" ", "_")
        logger_name = "tui.screen." + screen_key
        self.logger = logging.getLogger(logger_name)

    def compose(self):
        """Compose the base screen layout.

        Override compose_content() in subclasses to add
        screen-specific content.
        """
        if self.SHOW_HEADER:
            yield Header()

        yield from self.compose_content()

        if self.SHOW_FOOTER:
            yield Footer()

    def compose_content(self):
        """Compose screen-specific content.

        Override this method in subclasses to add widgets.
        """
        yield Container()

    async def on_mount(self):
        """Called when screen is mounted."""
        self.logger.debug(f"Screen mounted: {self.SCREEN_TITLE}")
        await self.on_screen_mount()

    async def on_screen_mount(self):
        """Hook for subclasses to perform actions on mount.

        Override this instead of on_mount() in subclasses.
        """
        pass

    async def on_show(self):
        """Called when screen is shown."""
        self.logger.debug(f"Screen shown: {self.SCREEN_TITLE}")
        await self.refresh_data()

    async def refresh_data(self):
        """Refresh screen data.

        Override this method to update screen content from external sources.
        """
        pass

    def action_go_back(self):
        """Navigate back to previous screen."""
        self.logger.debug(f"Going back from: {self.SCREEN_TITLE}")
        self.app.pop_screen()

    async def show_notification(
        self, message: str, severity: str = "information"
    ):
        """Show a notification to the user.

        Args:
            message: Notification message
            severity: Severity level (information, warning, error, success)
        """
        # Use app's notification system if available
        if hasattr(self.app, "notify"):
            self.app.notify(message, severity=severity)

    async def show_error(self, message: str):
        """Show an error notification.

        Args:
            message: Error message
        """
        await self.show_notification(message, severity="error")

    async def show_success(self, message: str):
        """Show a success notification.

        Args:
            message: Success message
        """
        await self.show_notification(message, severity="success")
