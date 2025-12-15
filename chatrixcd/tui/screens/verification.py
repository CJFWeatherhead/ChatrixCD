"""Device verification screen for TUI."""

import asyncio
from typing import Any, Dict, List

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from .base import BaseScreen


class VerificationScreen(BaseScreen):
    """Screen for managing device verification and cross-verification."""

    SCREEN_TITLE = "Device Verification"

    CSS = """
    .verification-container {
        width: 100%;
        height: 100%;
        layout: vertical;
    }

    .section-header {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    .devices-section {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        border: solid $primary;
    }

    .pending-section {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        border: solid $accent;
    }

    .actions-section {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
        padding: 1;
        border: solid $surface;
    }

    .device-table {
        width: 100%;
        height: auto;
    }

    .pending-table {
        width: 100%;
        height: auto;
    }

    .verification-buttons {
        width: 100%;
        height: auto;
        layout: horizontal;
    }

    .verification-buttons > * {
        height: auto;
        margin: 0 1 0 0;
    }

    .emoji-display {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 0 0 1 0;
        text-align: center;
        width: 100%;
        height: auto;
    }

    .emoji-list {
        font-size: 1.2;
        margin: 0 0 1 0;
        width: 100%;
        height: auto;
    }

    .verification-status {
        text-align: center;
        padding: 1;
        width: 100%;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "back", "Back to Menu"),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize verification screen."""
        super().__init__(*args, **kwargs)
        self.verification_manager = None
        self.current_verification = None
        self.emoji_list = []

    def compose_content(self):
        """Compose verification screen content."""
        with Container(classes="verification-container"):
            yield Static("[bold cyan]Device Verification[/bold cyan]", classes="section-header")

            # Verified devices section
            with Vertical(classes="devices-section"):
                yield Static("[bold]Verified Devices[/bold]", classes="section-header")
                yield DataTable(id="verified-devices-table", classes="device-table")

            # Unverified devices section
            with Vertical(classes="devices-section"):
                yield Static("[bold]Unverified Devices[/bold]", classes="section-header")
                yield DataTable(id="unverified-devices-table", classes="device-table")

            # Pending verifications section
            with Vertical(classes="pending-section"):
                yield Static(
                    "[bold yellow]Pending Verifications[/bold yellow]",
                    classes="section-header",
                )
                yield DataTable(id="pending-table", classes="pending-table")

            # Actions section
            with Vertical(classes="actions-section"):
                yield Static("[bold]Actions[/bold]", classes="section-header")

                with Horizontal(classes="verification-buttons"):
                    yield Button(
                        "Start Verification",
                        id="start-verification-btn",
                        variant="primary",
                    )
                    yield Button("Accept Pending", id="accept-pending-btn", variant="success")
                    yield Button("Reject Pending", id="reject-pending-btn", variant="error")
                    yield Button("Cross-Verify Bots", id="cross-verify-btn", variant="warning")

                # Emoji verification display (shown during active verification)
                with Vertical(id="emoji-container", classes="emoji-display"):
                    yield Static("", id="emoji-status", classes="verification-status")
                    yield Static("", id="emoji-list-display", classes="emoji-list")
                    with Horizontal(classes="verification-buttons"):
                        yield Button("✅ Match", id="confirm-match-btn", variant="success")
                        yield Button("❌ Don't Match", id="confirm-no-match-btn", variant="error")

    async def on_screen_mount(self):
        """Initialize verification screen."""
        # Initialize verification manager
        if self.tui_app.bot and self.tui_app.bot.client:
            from ...verification import DeviceVerificationManager

            self.verification_manager = DeviceVerificationManager(self.tui_app.bot.client)

        await self.refresh_data()
        self.set_interval(5.0, self.refresh_data)

        # Hide emoji container initially
        emoji_container = self.query_one("#emoji-container")
        emoji_container.display = False

    async def refresh_data(self):
        """Refresh verification data."""
        if not self.verification_manager:
            return

        try:
            # Update verified devices table
            verified_table = self.query_one("#verified-devices-table", DataTable)
            await self._populate_devices_table(
                verified_table, await self.verification_manager.get_verified_devices()
            )

            # Update unverified devices table
            unverified_table = self.query_one("#unverified-devices-table", DataTable)
            await self._populate_devices_table(
                unverified_table,
                await self.verification_manager.get_unverified_devices(),
            )

            # Update pending verifications table
            pending_table = self.query_one("#pending-table", DataTable)
            await self._populate_pending_table(
                pending_table,
                await self.verification_manager.get_pending_verifications(),
            )

        except Exception as e:
            self.logger.error(f"Error refreshing verification data: {e}")
            await self.show_error(f"Failed to refresh verification data: {e}")

    async def _populate_devices_table(self, table: DataTable, devices: List[Dict[str, Any]]):
        """Populate a devices table."""
        # Clear existing data
        table.clear()

        # Set up columns
        table.add_columns("User", "Device", "Name", "Status")

        # Add device rows
        for device in devices:
            user_id = device.get("user_id", "Unknown")
            device_id = device.get("device_id", "Unknown")
            device_name = device.get("device_name", "Unknown")
            trust_state = device.get("trust_state", "Unknown")

            # Shorten user ID for display
            user_display = user_id.split(":")[0] if ":" in user_id else user_id
            if len(user_display) > 20:
                user_display = user_display[:17] + "..."

            # Shorten device ID
            device_display = device_id[:8] + "..." if len(device_id) > 8 else device_id

            table.add_row(user_display, device_display, device_name, trust_state)

    async def _populate_pending_table(self, table: DataTable, pending: List[Dict[str, Any]]):
        """Populate pending verifications table."""
        # Clear existing data
        table.clear()

        # Set up columns
        table.add_columns("User", "Device", "Type", "Action")

        # Add pending rows
        for verification in pending:
            user_id = verification.get("user_id", "Unknown")
            device_id = verification.get("device_id", "Unknown")
            verification_type = verification.get("type", "Unknown")

            # Shorten user ID for display
            user_display = user_id.split(":")[0] if ":" in user_id else user_id
            if len(user_display) > 20:
                user_display = user_display[:17] + "..."

            # Shorten device ID
            device_display = device_id[:8] + "..." if len(device_id) > 8 else device_id

            table.add_row(user_display, device_display, verification_type, "Pending")

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "start-verification-btn":
            await self._start_verification()
        elif button_id == "accept-pending-btn":
            await self._accept_pending_verification()
        elif button_id == "reject-pending-btn":
            await self._reject_pending_verification()
        elif button_id == "cross-verify-btn":
            await self._cross_verify_bots()
        elif button_id == "confirm-match-btn":
            await self._confirm_verification_match(True)
        elif button_id == "confirm-no-match-btn":
            await self._confirm_verification_match(False)

    async def _start_verification(self):
        """Start verification with selected unverified device."""
        try:
            unverified_table = self.query_one("#unverified-devices-table", DataTable)
            if not unverified_table.rows:
                await self.show_error("No unverified devices available")
                return

            # For now, start with the first unverified device
            # TODO: Add device selection UI
            unverified_devices = await self.verification_manager.get_unverified_devices()
            if not unverified_devices:
                await self.show_error("No unverified devices found")
                return

            device_info = unverified_devices[0]  # Start with first device

            # Start interactive verification
            success = await self.verification_manager.verify_device_interactive(
                device_info, self._display_emojis_callback
            )

            if success:
                await self.show_success(f"Successfully verified device {device_info['device_id']}")
                await self.refresh_data()
            else:
                await self.show_error("Verification failed or was cancelled")

        except Exception as e:
            self.logger.error(f"Error starting verification: {e}")
            await self.show_error(f"Failed to start verification: {e}")

    async def _accept_pending_verification(self):
        """Accept a pending verification request."""
        try:
            pending = await self.verification_manager.get_pending_verifications()
            if not pending:
                await self.show_error("No pending verifications")
                return

            # Accept the first pending verification
            verification_info = pending[0]

            success = await self.verification_manager.verify_pending_interactive(
                verification_info, self._display_emojis_callback
            )

            if success:
                await self.show_success("Verification accepted successfully")
                await self.refresh_data()
            else:
                await self.show_error("Verification failed")

        except Exception as e:
            self.logger.error(f"Error accepting pending verification: {e}")
            await self.show_error(f"Failed to accept verification: {e}")

    async def _reject_pending_verification(self):
        """Reject a pending verification request."""
        try:
            pending = await self.verification_manager.get_pending_verifications()
            if not pending:
                await self.show_error("No pending verifications")
                return

            # Reject the first pending verification
            verification_info = pending[0]
            verification = verification_info["verification"]

            if await self.verification_manager.reject_verification(verification):
                await self.show_success("Verification rejected")
                await self.refresh_data()
            else:
                await self.show_error("Failed to reject verification")

        except Exception as e:
            self.logger.error(f"Error rejecting pending verification: {e}")
            await self.show_error(f"Failed to reject verification: {e}")

    async def _cross_verify_bots(self):
        """Cross-verify with other ChatrixCD bots."""
        try:
            # Get current room members (this is a simplified approach)
            # In a real implementation, you'd get this from the current room context
            room_members = []
            if self.tui_app.bot and self.tui_app.bot.client and self.tui_app.bot.client.rooms:
                # Get members from the first room (simplified)
                for room in self.tui_app.bot.client.rooms.values():
                    room_members = list(room.users.keys())
                    break

            started_count = await self.verification_manager.cross_verify_with_bots(room_members)

            if started_count > 0:
                await self.show_success(
                    f"Started cross-verification with {started_count} bot devices"
                )
                await self.refresh_data()
            else:
                await self.show_info("No other bots found for cross-verification")

        except Exception as e:
            self.logger.error(f"Error during cross-verification: {e}")
            await self.show_error(f"Cross-verification failed: {e}")

    async def _display_emojis_callback(self, emoji_list: List[tuple]) -> bool:
        """Display emojis for verification and wait for user confirmation."""
        self.emoji_list = emoji_list

        # Show emoji container
        emoji_container = self.query_one("#emoji-container")
        emoji_container.display = True

        # Update emoji display
        emoji_status = self.query_one("#emoji-status", Static)
        emoji_status.update(
            "[bold yellow]Verify Device[/bold yellow]\nCompare these emojis with the other device:"
        )

        emoji_display = self.query_one("#emoji-list-display", Static)
        emoji_text = "\n".join([f"{emoji} {name}" for emoji, name in emoji_list])
        emoji_display.update(emoji_text)

        # Create a future to wait for user response
        self.verification_future = asyncio.Future()

        try:
            # Wait for user response with timeout
            result = await asyncio.wait_for(self.verification_future, timeout=60.0)
            return result
        except asyncio.TimeoutError:
            await self.show_error("Verification timeout - please try again")
            return False
        finally:
            # Hide emoji container
            emoji_container.display = False
            # Reset displays
            emoji_status.update("")
            emoji_display.update("")

    async def _confirm_verification_match(self, matches: bool):
        """Handle user's emoji match confirmation."""
        # Set the future result if it exists
        if hasattr(self, "verification_future") and not self.verification_future.done():
            self.verification_future.set_result(matches)

        # Hide emoji container
        emoji_container = self.query_one("#emoji-container")
        emoji_container.display = False

        # Reset emoji display
        emoji_status = self.query_one("#emoji-status", Static)
        emoji_status.update("")

        emoji_display = self.query_one("#emoji-list-display", Static)
        emoji_display.update("")

        # Show feedback
        if matches:
            await self.show_success("Emojis confirmed - completing verification...")
        else:
            await self.show_error("Emojis don't match - verification cancelled")

    def action_refresh(self):
        """Manually refresh verification data."""
        self.app.call_later(self.refresh_data)

    def action_back(self):
        """Go back to main menu."""
        self.app.pop_screen()
