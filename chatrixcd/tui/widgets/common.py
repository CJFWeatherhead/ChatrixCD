"""Common reusable widgets for TUI."""

from typing import Optional, Callable, Any
from textual.widget import Widget
from textual.widgets import Static, Button, DataTable, Input, Select, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from .base import BaseWidget


class StatusIndicator(Static):
    """Widget showing connection/service status with color indicator."""
    
    DEFAULT_CSS = """
    StatusIndicator {
        height: auto;
        width: auto;
    }
    """
    
    def __init__(self, service_name: str = "Service", *args, **kwargs):
        """Initialize status indicator.
        
        Args:
            service_name: Name of the service
        """
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self._status = "Unknown"
        
    @property
    def status(self) -> str:
        """Get current status."""
        return self._status
        
    @status.setter
    def status(self, value: str):
        """Set status and update display."""
        self._status = value
        self.update(self._render_status())
        
    def _render_status(self) -> str:
        """Render status with color."""
        color_map = {
            "connected": "green",
            "disconnected": "red",
            "connecting": "yellow",
            "unknown": "grey",
        }
        
        color = color_map.get(self._status.lower(), "white")
        return f"[bold]{self.service_name}:[/bold] [{color}]●[/{color}] {self._status}"
        
    def on_mount(self):
        """Update display when mounted."""
        self.update(self._render_status())


class MetricDisplay(BaseWidget):
    """Widget for displaying a metric with label and value."""
    
    label: reactive[str] = reactive("Metric")
    value: reactive[str | int] = reactive(0)
    icon: reactive[str] = reactive("")
    
    def __init__(
        self,
        label: str = "Metric",
        value: str | int = 0,
        icon: str = "",
        *args,
        **kwargs
    ):
        """Initialize metric display.
        
        Args:
            label: Metric label
            value: Initial value
            icon: Optional icon/emoji
        """
        super().__init__(*args, **kwargs)
        self.label = label
        self.value = value
        self.icon = icon
    
    def render(self) -> str:
        """Render the metric display."""
        icon_str = f"{self.icon} " if self.icon else ""
        return f"[bold]{icon_str}{self.label}:[/bold] {self.value}"


class ActionButton(Button):
    """Enhanced button with consistent styling and callbacks."""
    
    def __init__(
        self,
        label: str,
        action: Optional[Callable] = None,
        variant: str = "default",
        icon: str = "",
        *args,
        **kwargs
    ):
        """Initialize action button.
        
        Args:
            label: Button text
            action: Callback function when button is pressed
            variant: Button style variant
            icon: Optional icon/emoji
        """
        button_label = f"{icon} {label}" if icon else label
        super().__init__(button_label, variant=variant, *args, **kwargs)
        self.action_callback = action
        
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button press."""
        if self.action_callback:
            await self.action_callback()


class ConfirmDialog(Container):
    """Modal confirmation dialog."""
    
    def __init__(
        self,
        message: str,
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        **kwargs
    ):
        """Initialize confirmation dialog.
        
        Args:
            message: Message to display
            on_confirm: Callback when confirmed
            on_cancel: Callback when canceled
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
        """
        super().__init__(**kwargs)
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        
    def compose(self):
        """Compose the dialog."""
        with Vertical(classes="dialog-container"):
            yield Static(self.message, classes="dialog-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button(self.confirm_text, variant="primary", id="confirm")
                yield Button(self.cancel_text, variant="default", id="cancel")
                
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button press."""
        if event.button.id == "confirm":
            await self.on_confirm()
        elif event.button.id == "cancel" and self.on_cancel:
            await self.on_cancel()


class FormField(Container):
    """Form field with label and input."""
    
    def __init__(
        self,
        label: str,
        field_type: str = "text",
        default_value: str = "",
        placeholder: str = "",
        validator: Optional[Callable[[str], bool]] = None,
        **kwargs
    ):
        """Initialize form field.
        
        Args:
            label: Field label
            field_type: Type of field (text, password, number)
            default_value: Default value
            placeholder: Placeholder text
            validator: Validation function
        """
        super().__init__(**kwargs)
        self.label_text = label
        self.field_type = field_type
        self.default_value = default_value
        self.placeholder_text = placeholder
        self.validator = validator
        
    def compose(self):
        """Compose the form field."""
        yield Label(self.label_text, classes="field-label")
        yield Input(
            value=self.default_value,
            placeholder=self.placeholder_text,
            password=self.field_type == "password",
            classes="field-input"
        )
        
    def get_value(self) -> str:
        """Get the current field value."""
        input_widget = self.query_one(Input)
        return input_widget.value
        
    def set_value(self, value: str):
        """Set the field value."""
        input_widget = self.query_one(Input)
        input_widget.value = value
        
    def validate(self) -> bool:
        """Validate the field value."""
        if self.validator:
            return self.validator(self.get_value())
        return True


class DataGrid(Container):
    """Enhanced data table with sorting and filtering."""
    
    def __init__(
        self,
        columns: list[str],
        sortable: bool = True,
        filterable: bool = False,
        **kwargs
    ):
        """Initialize data grid.
        
        Args:
            columns: Column names
            sortable: Whether columns can be sorted
            filterable: Whether data can be filtered
        """
        super().__init__(**kwargs)
        self.columns = columns
        self.sortable = sortable
        self.filterable = filterable
        self._data = []
        
    def compose(self):
        """Compose the data grid."""
        if self.filterable:
            yield Input(placeholder="Filter...", classes="grid-filter")
        yield DataTable(id="data-table", classes="data-grid")
        
    def on_mount(self):
        """Set up the data table."""
        table = self.query_one(DataTable)
        for column in self.columns:
            table.add_column(column, key=column.lower().replace(" ", "_"))
            
    def add_row(self, *cells):
        """Add a row to the table."""
        table = self.query_one(DataTable)
        table.add_row(*cells)
        self._data.append(cells)
        
    def clear(self):
        """Clear all rows."""
        table = self.query_one(DataTable)
        table.clear()
        self._data = []
        
    def refresh_data(self, data: list[tuple]):
        """Refresh table with new data."""
        self.clear()
        for row in data:
            self.add_row(*row)


class NotificationDisplay(Static):
    """Widget for displaying notifications."""
    
    def show_notification(self, message: str, severity: str = "information"):
        """Display a notification.
        
        Args:
            message: Notification message
            severity: Severity level (information, warning, error, success)
        """
        color_map = {
            "information": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        }
        
        icon_map = {
            "information": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        
        color = color_map.get(severity, "white")
        icon = icon_map.get(severity, "•")
        
        self.update(f"[{color}]{icon} {message}[/{color}]")
        
        # Auto-hide after 5 seconds
        self.set_timer(5.0, lambda: self.update(""))
