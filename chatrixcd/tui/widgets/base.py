"""Base widget classes for TUI."""

from textual.widget import Widget
from textual.reactive import reactive


class BaseWidget(Widget):
    """Base class for all TUI widgets.

    Provides common functionality and consistent interface.
    """

    can_focus: bool = True

    def __init__(self, *args, **kwargs):
        """Initialize base widget."""
        super().__init__(*args, **kwargs)

    async def refresh_data(self):
        """Refresh widget data.

        Override this method to update widget content from external sources.
        """
        pass


class StatusWidget(BaseWidget):
    """Widget for displaying status information."""

    status: reactive[str] = reactive("Unknown")
    status_color: reactive[str] = reactive("white")

    def render(self) -> str:
        """Render the status widget."""
        return f"[{self.status_color}]{self.status}[/{self.status_color}]"
