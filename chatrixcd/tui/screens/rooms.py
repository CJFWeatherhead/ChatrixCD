"""Rooms screen showing Matrix rooms."""

from textual.containers import Container, ScrollableContainer
from textual.widgets import Static
from .base import BaseScreen
from ..widgets.common import DataGrid


class RoomsScreen(BaseScreen):
    """Screen showing Matrix rooms the bot has joined."""

    SCREEN_TITLE = "Rooms"

    def __init__(self, rooms=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow direct instantiation in tests with a rooms list
        self.rooms = rooms

    def compose_content(self):
        """Compose rooms screen content."""
        with Container(classes="rooms-container"):
            yield Static(
                "[bold cyan]Matrix Rooms[/bold cyan]", classes="section-header"
            )
            yield Static("Rooms the bot has joined:", classes="description")

            yield DataGrid(
                columns=["Room Name", "Room ID", "Members", "Encrypted"],
                id="rooms-table",
            )

    async def on_screen_mount(self):
        """Load rooms data."""
        await self.refresh_data()

    async def refresh_data(self):
        """Refresh rooms data."""
        try:
            table = self.query_one("#rooms-table", DataGrid)
            table.clear()

            if not self.tui_app.bot or not self.tui_app.bot.client:
                return

            client = self.tui_app.bot.client

            if not hasattr(client, "rooms") or not client.rooms:
                table.add_row("No rooms", "-", "-", "-")
                return

            # Add each room to table
            for room_id, room in client.rooms.items():
                room_name = room.display_name or room.name or "Unnamed Room"
                member_count = len(room.users)
                encrypted = "Yes" if room.encrypted else "No"

                table.add_row(room_name, room_id, str(member_count), encrypted)

        except Exception as e:
            self.logger.error(f"Error refreshing rooms: {e}")
            await self.show_error(f"Failed to load rooms: {e}")
