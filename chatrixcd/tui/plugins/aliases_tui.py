"""Example TUI integration for aliases plugin."""

from textual.containers import (
    Container,
    Vertical,
    Horizontal,
)
from textual.widgets import Static, Button, Input, Label
from textual.binding import Binding
from textual.screen import ModalScreen

from chatrixcd.tui.screens.base import BaseScreen
from chatrixcd.tui.plugin_integration import (
    PluginTUIExtension,
    PluginScreenMixin,
)
from chatrixcd.tui.widgets.common import DataGrid


class AliasInputModal(ModalScreen):
    """Modal for adding a new alias."""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    def __init__(self, on_submit, **kwargs):
        """Initialize alias input modal.

        Args:
            on_submit: Callback function(alias_name, command)
        """
        super().__init__(**kwargs)
        self.on_submit = on_submit

    def compose(self):
        """Compose the modal."""
        with Container(classes="modal-container"):
            yield Static("[bold]Add New Alias[/bold]", classes="modal-title")

            with Vertical(classes="modal-content"):
                yield Label("Alias Name (emoji supported):")
                yield Input(
                    placeholder="e.g., deploy or 🚀",
                    id="alias-name",
                    classes="modal-input",
                )

                yield Label("Command (without !cd prefix):")
                yield Input(
                    placeholder="e.g., run 1 5",
                    id="alias-command",
                    classes="modal-input",
                )

            with Horizontal(classes="modal-buttons"):
                yield Button("Create", variant="primary", id="create-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button press."""
        if event.button.id == "create-button":
            alias_name = self.query_one("#alias-name", Input).value.strip()
            command = self.query_one("#alias-command", Input).value.strip()

            if not alias_name or not command:
                self.app.notify("Both fields are required", severity="error")
                return

            await self.on_submit(alias_name, command)
            self.dismiss()

        elif event.button.id == "cancel-button":
            self.dismiss()


class AliasesScreen(BaseScreen, PluginScreenMixin):
    """Screen for managing command aliases."""

    SCREEN_TITLE = "Command Aliases"

    BINDINGS = [
        Binding("escape", "go_back", "Back", priority=True),
        Binding("b", "go_back", "Back"),
        Binding("a", "add_alias", "Add"),
        Binding("d", "delete_alias", "Delete"),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize aliases screen."""
        super().__init__(*args, **kwargs)
        self.selected_alias = None

    def compose_content(self):
        """Compose aliases screen content."""
        with Container(classes="aliases-container"):
            yield Static(
                "[bold cyan]Command Aliases[/bold cyan]",
                classes="section-header",
            )
            yield Static(
                "Manage command shortcuts. Press 'a' to add, 'd' to delete.",
                classes="description",
            )

            yield DataGrid(
                columns=["Alias", "Command", "Actions"], id="aliases-table"
            )

            with Horizontal(classes="action-buttons"):
                yield Button(
                    "Add Alias",
                    id="add-alias",
                    variant="primary",
                    classes="action-btn",
                )
                yield Button(
                    "Delete Selected",
                    id="delete-alias",
                    variant="error",
                    classes="action-btn",
                )
                yield Button(
                    "Refresh",
                    id="refresh",
                    variant="default",
                    classes="action-btn",
                )

    async def on_screen_mount(self):
        """Load aliases when screen mounts."""
        await self.refresh_data()

    async def refresh_data(self):
        """Refresh aliases data."""
        try:
            table = self.query_one("#aliases-table", DataGrid)
            table.clear()

            # Get aliases plugin
            plugin = self.get_plugin("aliases")
            if not plugin:
                table.add_row("Aliases plugin not loaded", "-", "-")
                return

            # Get aliases
            aliases = plugin.list_aliases()

            if not aliases:
                table.add_row("[dim]No aliases configured[/dim]", "-", "-")
                return

            # Add each alias to table
            for alias_name, command in aliases.items():
                table.add_row(
                    alias_name,
                    command,
                    "✏️ 🗑️",  # Edit/Delete icons (placeholder)
                )

        except Exception as e:
            self.logger.error(f"Error refreshing aliases: {e}")
            await self.show_error(f"Failed to load aliases: {e}")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "add-alias":
            await self.add_alias()
        elif event.button.id == "delete-alias":
            await self.delete_selected_alias()
        elif event.button.id == "refresh":
            await self.refresh_data()

    async def add_alias(self):
        """Show modal to add new alias."""

        async def on_submit(alias_name: str, command: str):
            """Handle alias creation."""
            try:
                plugin = self.get_plugin("aliases")
                if not plugin:
                    await self.show_error("Aliases plugin not loaded")
                    return

                # Validate command
                if not plugin.validate_command(command):
                    await self.show_error(f"Invalid command: {command}")
                    return

                # Add alias
                if plugin.add_alias(alias_name, command):
                    await self.show_success(f"Alias '{alias_name}' created")
                    await self.refresh_data()
                else:
                    await self.show_error(
                        f"Failed to create alias '{alias_name}'"
                    )

            except Exception as e:
                self.logger.error(f"Error adding alias: {e}")
                await self.show_error(f"Failed to add alias: {e}")

        self.app.push_screen(AliasInputModal(on_submit=on_submit))

    async def delete_selected_alias(self):
        """Delete the currently selected alias."""
        if not self.selected_alias:
            await self.show_error("No alias selected")
            return

        try:
            plugin = self.get_plugin("aliases")
            if not plugin:
                await self.show_error("Aliases plugin not loaded")
                return

            if plugin.remove_alias(self.selected_alias):
                await self.show_success(
                    f"Alias '{self.selected_alias}' deleted"
                )
                self.selected_alias = None
                await self.refresh_data()
            else:
                await self.show_error(
                    f"Failed to delete alias '{self.selected_alias}'"
                )

        except Exception as e:
            self.logger.error(f"Error deleting alias: {e}")
            await self.show_error(f"Failed to delete alias: {e}")

    def action_add_alias(self):
        """Add alias action."""
        self.app.call_later(self.add_alias)

    def action_delete_alias(self):
        """Delete alias action."""
        self.app.call_later(self.delete_selected_alias)


class AliasesPluginTUI(PluginTUIExtension):
    """TUI extension for aliases plugin."""

    async def register_tui_screens(self, registry, tui_app):
        """Register aliases management screen."""
        self._register_screen(
            registry=registry,
            name="aliases",
            screen_class=AliasesScreen,
            title="Command Aliases",
            key_binding="x",
            priority=25,
            category="core",
            icon="📝",
        )
