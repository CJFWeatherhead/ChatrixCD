"""Text User Interface for ChatrixCD bot.

This TUI implementation was developed with assistance from AI/LLM tools,
providing an interactive menu-driven interface for bot management and
device verification workflows.
"""

import asyncio
import logging
import time
import json
import qrcode
import io
from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label, Input, Select, TextArea, DataTable, Switch, OptionList
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import events
from textual.reactive import reactive
from chatrixcd.verification import DeviceVerificationManager

logger = logging.getLogger(__name__)


class BotStatusWidget(Static):
    """Widget to display bot status information."""
    
    matrix_status: reactive[str] = reactive("Disconnected")
    semaphore_status: reactive[str] = reactive("Unknown")
    uptime: reactive[str] = reactive("0s")
    messages_processed: reactive[int] = reactive(0)
    errors: reactive[int] = reactive(0)
    warnings: reactive[int] = reactive(0)
    
    def render(self) -> str:
        """Render the status widget."""
        return f"""[bold cyan]Bot Status[/bold cyan]

[bold]Matrix:[/bold] {self.matrix_status}
[bold]Semaphore:[/bold] {self.semaphore_status}
[bold]Uptime:[/bold] {self.uptime}

[bold cyan]Metrics[/bold cyan]
[bold]Messages Processed:[/bold] {self.messages_processed}
[bold]Errors:[/bold] {self.errors}
[bold]Warnings:[/bold] {self.warnings}
"""


class ActiveTasksWidget(Static):
    """Widget to display active tasks."""
    
    tasks: reactive[List[Dict[str, Any]]] = reactive([])
    
    def render(self) -> str:
        """Render the active tasks widget."""
        if not self.tasks:
            return "[bold cyan]Active Tasks[/bold cyan]\n\n[dim]No active tasks[/dim]"
        
        task_lines = ["[bold cyan]Active Tasks[/bold cyan]\n"]
        for task_info in self.tasks:
            task_id = task_info.get('task_id', 'Unknown')
            project_id = task_info.get('project_id', 'Unknown')
            status = task_info.get('status', 'Unknown')
            
            # Color code based on status
            if status == 'running':
                status_icon = "🔄"
                color = "yellow"
            elif status == 'success':
                status_icon = "✅"
                color = "green"
            elif status in ('error', 'stopped'):
                status_icon = "❌"
                color = "red"
            else:
                status_icon = "⏸️"
                color = "blue"
            
            task_lines.append(f"  {status_icon} Task {task_id} (Project {project_id}): [{color}]{status}[/{color}]")
        
        return "\n".join(task_lines)


class AdminsScreen(Screen):
    """Screen to display admin users."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, admins: List[str], **kwargs):
        super().__init__(**kwargs)
        self.admins = admins
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Admin Users[/bold cyan]\n", id="title")
            if not self.admins:
                yield Static("[dim]No admin users configured. All users have admin access.[/dim]")
            else:
                for admin in self.admins:
                    yield Static(f"• {admin}")
        yield Footer()


class AliasesScreen(Screen):
    """Screen to manage command aliases."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
        Binding("a", "add_alias", "Add"),
        Binding("d", "delete_alias", "Delete"),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
        self.selected_alias = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with ScrollableContainer():
            yield Static("[bold cyan]Command Aliases[/bold cyan]\n", id="title")
            yield Static("[dim]Press 'a' to add, 'd' to delete. Only valid !cd commands can be aliased.[/dim]\n")
            
            # Get aliases from command handler
            if self.tui_app.bot and hasattr(self.tui_app.bot, 'command_handler'):
                aliases = self.tui_app.bot.command_handler.alias_manager.list_aliases()
                
                if not aliases:
                    yield Static("[dim]No aliases configured.[/dim]\n")
                else:
                    yield Static("[bold]Current Aliases:[/bold]\n")
                    for alias, command in aliases.items():
                        yield Button(f"{alias} → {command}", id=f"alias_{alias}")
            else:
                yield Static("[dim]Bot not initialized.[/dim]\n")
            
            yield Static("\n[bold]Actions:[/bold]")
            yield Button("Add Alias [a]", id="add_alias_button", variant="primary")
            yield Button("Delete Selected [d]", id="delete_alias_button", variant="error")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id.startswith("alias_"):
            # Select this alias
            alias_name = button_id[6:]
            self.selected_alias = alias_name
            # Update button styles to show selection
            for button in self.query(Button):
                if button.id == button_id:
                    button.variant = "success"
                elif button.id and button.id.startswith("alias_"):
                    button.variant = "default"
        elif button_id == "add_alias_button":
            await self.add_alias()
        elif button_id == "delete_alias_button":
            await self.delete_alias()
    
    async def action_add_alias(self):
        """Add a new alias."""
        await self.add_alias()
    
    async def action_delete_alias(self):
        """Delete selected alias."""
        await self.delete_alias()
    
    async def add_alias(self):
        """Prompt to add a new alias."""
        from textual.widgets import Input
        
        class AliasInputScreen(ModalScreen):
            """Modal screen for adding an alias."""
            
            def __init__(self, alias_manager, **kwargs):
                super().__init__(**kwargs)
                self.alias_manager = alias_manager
            
            def compose(self) -> ComposeResult:
                """Create child widgets."""
                with Container():
                    yield Static("[bold cyan]Add New Alias[/bold cyan]\n")
                    yield Static("Alias name (e.g., 'deploy'):")
                    yield Input(placeholder="alias-name", id="alias_name")
                    yield Static("\nCommand (e.g., 'run 1 5'):")
                    yield Input(placeholder="run 1 5", id="alias_command")
                    yield Static("\n[dim]Valid commands: help, projects, templates, run, status, stop, logs, ping, info[/dim]\n")
                    yield Button("Create", id="create", variant="primary")
                    yield Button("Cancel", id="cancel")
            
            async def on_button_pressed(self, event: Button.Pressed) -> None:
                """Handle button presses."""
                if event.button.id == "create":
                    name_input = self.query_one("#alias_name", Input)
                    command_input = self.query_one("#alias_command", Input)
                    
                    alias_name = name_input.value.strip()
                    alias_command = command_input.value.strip()
                    
                    if not alias_name or not alias_command:
                        self.app.push_screen(
                            MessageScreen("Both alias name and command are required.")
                        )
                        return
                    
                    # Validate command
                    if not self.alias_manager.validate_command(alias_command):
                        self.app.push_screen(
                            MessageScreen(
                                f"Invalid command: {alias_command}\n\n"
                                "Valid commands: help, projects, templates, run, status, stop, logs, ping, info"
                            )
                        )
                        return
                    
                    # Add alias
                    success = self.alias_manager.add_alias(alias_name, alias_command)
                    
                    if success:
                        self.app.push_screen(
                            MessageScreen(f"✅ Alias '{alias_name}' created successfully!")
                        )
                        self.dismiss()
                    else:
                        self.app.push_screen(
                            MessageScreen(
                                f"❌ Failed to create alias.\n\n"
                                f"'{alias_name}' may conflict with a built-in command."
                            )
                        )
                elif event.button.id == "cancel":
                    self.dismiss()
        
        if self.tui_app.bot and hasattr(self.tui_app.bot, 'command_handler'):
            alias_manager = self.tui_app.bot.command_handler.alias_manager
            self.app.push_screen(AliasInputScreen(alias_manager))
        else:
            self.app.push_screen(MessageScreen("Bot not initialized."))
    
    async def delete_alias(self):
        """Delete the selected alias."""
        if not self.selected_alias:
            self.app.push_screen(MessageScreen("No alias selected. Click on an alias to select it."))
            return
        
        if self.tui_app.bot and hasattr(self.tui_app.bot, 'command_handler'):
            alias_manager = self.tui_app.bot.command_handler.alias_manager
            success = alias_manager.remove_alias(self.selected_alias)
            
            if success:
                self.app.push_screen(
                    MessageScreen(f"✅ Alias '{self.selected_alias}' deleted successfully!")
                )
                self.selected_alias = None
                # Refresh screen
                self.app.pop_screen()
                self.app.push_screen(AliasesScreen(self.tui_app))
            else:
                self.app.push_screen(
                    MessageScreen(f"❌ Failed to delete alias '{self.selected_alias}'.")
                )
        else:
            self.app.push_screen(MessageScreen("Bot not initialized."))


class RoomsScreen(Screen):
    """Screen to display rooms the bot is in."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, rooms: List[Dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        self.rooms = rooms
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Rooms[/bold cyan]\n", id="title")
            if self.rooms:
                for room in self.rooms:
                    yield Static(f"  • {room.get('name', 'Unknown')} ({room.get('id', 'Unknown')})")
            else:
                yield Static("[yellow]Not in any rooms[/yellow]")
        yield Footer()


class SessionsScreen(Screen):
    """Screen for session management."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with ScrollableContainer():
            yield Static("[bold cyan]Session Management[/bold cyan]\n", id="title")
            yield Button("View Encryption Sessions", id="view_sessions", variant="primary")
            yield Button("View Pending Verification Requests", id="view_pending_verifications")
            yield Button("Verify Device (Emoji)", id="verify_emoji")
            yield Button("Verify Device (QR Code)", id="verify_qr")
            yield Button("Show Fingerprint", id="show_fingerprint")
            yield Button("Reset Olm Sessions", id="reset_olm", variant="warning")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "view_sessions":
            await self.show_sessions_list()
        elif event.button.id == "view_pending_verifications":
            await self.show_pending_verifications()
        elif event.button.id == "verify_emoji":
            await self.show_emoji_verification()
        elif event.button.id == "verify_qr":
            await self.show_qr_verification()
        elif event.button.id == "show_fingerprint":
            await self.show_device_fingerprint()
        elif event.button.id == "reset_olm":
            await self.reset_olm_sessions()
    
    async def show_pending_verifications(self):
        """Display list of pending verification requests with action buttons."""
        if not self.tui_app.bot or not self.tui_app.bot.client or not self.tui_app.bot.client.olm:
            self.app.push_screen(MessageScreen("Encryption is not enabled."))
            return
        
        # Use verification manager to get pending verifications
        verification_manager = self.tui_app.bot.verification_manager
        pending = await verification_manager.get_pending_verifications()
        
        if not pending:
            self.app.push_screen(MessageScreen(
                "[bold cyan]Pending Verification Requests[/bold cyan]\n\n"
                "No pending verification requests.\n\n"
                "[dim]When another device initiates verification with this bot,\n"
                "it will appear here. You can then complete the verification\n"
                "by clicking the 'Verify' button below.[/dim]"
            ))
            return
        
        # Show interactive screen with buttons for each request
        await self._show_pending_verifications_screen(pending)
    
    async def _show_pending_verifications_screen(self, pending: List[Dict[str, Any]]):
        """Show interactive screen with pending verifications and action buttons.
        
        Args:
            pending: List of pending verification requests
        """
        from textual.screen import Screen as BaseScreen
        from nio.crypto import Sas
        
        class PendingVerificationsScreen(BaseScreen):
            """Screen showing pending verification requests with action buttons."""
            
            BINDINGS = [
                Binding("escape", "app.pop_screen", "Back", priority=True),
            ]
            
            def __init__(self, parent_sessions_screen, pending: List[Dict[str, Any]], **kwargs):
                super().__init__(**kwargs)
                self.parent_sessions_screen = parent_sessions_screen
                self.pending = pending
            
            def compose(self) -> ComposeResult:
                yield Header()
                with ScrollableContainer():
                    yield Static("[bold cyan]Pending Verification Requests[/bold cyan]\n", id="title")
                    yield Static(f"[bold]{len(self.pending)} pending request(s)[/bold]\n")
                    
                    for idx, ver in enumerate(self.pending):
                        yield Static(f"\n[bold]Request {idx + 1}:[/bold]")
                        yield Static(f"  User: {ver['user_id']}")
                        yield Static(f"  Device: {ver['device_id']}")
                        yield Static(f"  Transaction: {ver['transaction_id'][:16]}...")
                        yield Static(f"  Type: {ver['type']}\n")
                        yield Button(f"✅ Verify Request {idx + 1}", id=f"verify_{idx}", variant="primary")
                    
                    yield Static("\n[dim]Click 'Verify' to respond to a verification request.[/dim]")
                yield Footer()
            
            async def on_button_pressed(self, event: Button.Pressed) -> None:
                button_id = event.button.id
                if button_id.startswith("verify_"):
                    idx = int(button_id.split("_")[1])
                    ver_info = self.pending[idx]
                    await self.start_verification_for_pending(ver_info)
            
            async def start_verification_for_pending(self, ver_info: Dict[str, Any]):
                """Start verification for a pending request.
                
                Args:
                    ver_info: Verification information dictionary
                """
                from nio.crypto import Sas, SasState
                
                try:
                    client = self.parent_sessions_screen.tui_app.bot.client
                    verification = ver_info['verification']
                    
                    # Check if this is a SAS verification
                    if not isinstance(verification, Sas):
                        self.app.push_screen(MessageScreen(
                            f"Unsupported verification type: {ver_info['type']}\n\n"
                            "Only SAS (emoji) verification is currently supported."
                        ))
                        return
                    
                    sas = verification
                    
                    # If we didn't start this verification, accept it
                    if not sas.we_started_it and sas.state == SasState.created:
                        await client.accept_key_verification(sas.transaction_id)
                        await asyncio.sleep(0.5)
                    
                    # Wait for key exchange
                    max_wait = 10
                    wait_time = 0
                    while not sas.other_key_set and wait_time < max_wait:
                        await asyncio.sleep(0.5)
                        wait_time += 0.5
                    
                    if not sas.other_key_set:
                        self.app.push_screen(MessageScreen(
                            "Verification timeout: Did not receive the other device's key.\n\n"
                            "Please ensure the other device has accepted the verification request."
                        ))
                        return
                    
                    # Get emoji sequence
                    try:
                        emoji_list = sas.get_emoji()
                        emoji_display = " ".join([f"{emoji} ({desc})" for emoji, desc in emoji_list])
                    except Exception as e:
                        logger.error(f"Error getting emojis: {e}")
                        self.app.push_screen(MessageScreen(
                            f"Error getting emojis: {e}\n\n"
                            f"SAS state: {sas.state.name if hasattr(sas.state, 'name') else sas.state}\n"
                            f"Other key set: {sas.other_key_set}"
                        ))
                        return
                    
                    # Show verification screen
                    device_info = {
                        'user_id': ver_info['user_id'],
                        'device_id': ver_info['device_id'],
                        'device_name': f"Device {ver_info['device_id']}"
                    }
                    
                    # Create inline verification screen (similar to the one in device selection)
                    class VerificationScreen(ModalScreen):
                        BINDINGS = [
                            Binding("escape", "app.pop_screen", "Cancel", priority=True),
                        ]
                        
                        def __init__(self, pending_screen, sas, emoji_display: str, device_info: Dict[str, Any], **kwargs):
                            super().__init__(**kwargs)
                            self.pending_screen = pending_screen
                            self.sas = sas
                            self.emoji_display = emoji_display
                            self.device_info = device_info
                        
                        def compose(self) -> ComposeResult:
                            yield Header()
                            with Container():
                                yield Static("[bold cyan]Emoji Verification[/bold cyan]\n", id="title")
                                yield Static(f"[bold]Verifying device:[/bold]\n{self.device_info['user_id']}\n{self.device_info['device_name']}\n")
                                yield Static(f"[bold]Compare these emojis with the other device:[/bold]\n\n{self.emoji_display}\n")
                                yield Static("[bold]Do the emojis match?[/bold]\n")
                                yield Button("✅ Yes, they match", id="confirm", variant="success")
                                yield Button("❌ No, they don't match", id="reject", variant="error")
                            yield Footer()
                        
                        async def on_button_pressed(self, event: Button.Pressed) -> None:
                            if event.button.id == "confirm":
                                await self.confirm_verification()
                            elif event.button.id == "reject":
                                await self.reject_verification()
                        
                        async def confirm_verification(self):
                            """Confirm the SAS verification."""
                            try:
                                if not self.sas.other_key_set:
                                    self.app.push_screen(MessageScreen(
                                        "Cannot confirm verification: Key exchange not complete.\n\n"
                                        "The other device has not sent its key yet. Please wait or try again."
                                    ))
                                    return
                                
                                self.sas.accept_sas()
                                client = self.pending_screen.parent_sessions_screen.tui_app.bot.client
                                await client.send_to_device_messages()
                                
                                self.app.push_screen(MessageScreen("✅ Verification successful!\n\nThe device has been verified and marked as trusted."))
                                self.dismiss()
                                
                            except Exception as e:
                                logger.error(f"Error confirming verification: {e}")
                                self.app.push_screen(MessageScreen(
                                    f"Error confirming verification: {e}\n\n"
                                    f"SAS state: {self.sas.state.name if hasattr(self.sas.state, 'name') else self.sas.state}\n"
                                    f"Other key set: {self.sas.other_key_set}"
                                ))
                        
                        async def reject_verification(self):
                            """Reject the SAS verification."""
                            try:
                                if not self.sas.other_key_set:
                                    self.app.push_screen(MessageScreen(
                                        "Cannot reject verification: Key exchange not complete.\n\n"
                                        "The other device has not sent its key yet. Please wait or try again."
                                    ))
                                    return
                                
                                self.sas.reject_sas()
                                client = self.pending_screen.parent_sessions_screen.tui_app.bot.client
                                await client.send_to_device_messages()
                                
                                self.app.push_screen(MessageScreen("❌ Verification rejected.\n\nThe emojis did not match. The device was not verified."))
                                self.dismiss()
                                
                            except Exception as e:
                                logger.error(f"Error rejecting verification: {e}")
                                self.app.push_screen(MessageScreen(
                                    f"Error rejecting verification: {e}\n\n"
                                    f"SAS state: {self.sas.state.name if hasattr(self.sas.state, 'name') else self.sas.state}\n"
                                    f"Other key set: {self.sas.other_key_set}"
                                ))
                    
                    self.app.push_screen(VerificationScreen(self, sas, emoji_display, device_info))
                    
                except Exception as e:
                    logger.error(f"Error starting verification: {e}")
                    self.app.push_screen(MessageScreen(f"Error starting verification: {e}"))
        
        self.app.push_screen(PendingVerificationsScreen(self, pending))
    
    async def show_sessions_list(self):
        """Display list of encryption sessions."""
        sessions_info = []
        
        if self.tui_app.bot and self.tui_app.bot.client and self.tui_app.bot.client.olm:
            try:
                # Get device store sessions
                device_store = self.tui_app.bot.client.device_store
                if device_store:
                    for user_id in device_store.users:
                        user_devices = device_store[user_id]
                        for device_id, device in user_devices.items():
                            sessions_info.append({
                                'user_id': user_id,
                                'device_id': device_id,
                                'device_name': getattr(device, 'display_name', 'Unknown'),
                                'verified': getattr(device, 'verified', False)
                            })
            except Exception as e:
                logger.error(f"Error retrieving sessions: {e}")
                self.app.push_screen(MessageScreen(f"Error retrieving sessions: {e}"))
                return
        
        if not sessions_info:
            self.app.push_screen(MessageScreen("No encryption sessions found.\n\nThis is normal if:\n• Encryption is not enabled\n• No encrypted messages have been exchanged\n• Store has been reset"))
            return
        
        # Create sessions display screen
        sessions_text = "[bold cyan]Encryption Sessions[/bold cyan]\n\n"
        for session in sessions_info:
            verified_icon = "✅" if session['verified'] else "⚠️"
            sessions_text += f"{verified_icon} {session['user_id']}\n"
            sessions_text += f"   Device: {session['device_name']} ({session['device_id']})\n"
            sessions_text += f"   Verified: {session['verified']}\n\n"
        
        self.app.push_screen(MessageScreen(sessions_text))
    
    async def show_emoji_verification(self):
        """Show emoji-based device verification using Matrix SDK."""
        if not self.tui_app.bot or not self.tui_app.bot.client or not self.tui_app.bot.client.olm:
            self.app.push_screen(MessageScreen("Encryption is not enabled. Cannot perform emoji verification."))
            return
        
        # Use verification manager to get unverified devices
        verification_manager = self.tui_app.bot.verification_manager
        unverified_devices = await verification_manager.get_unverified_devices()
        
        if not unverified_devices:
            self.app.push_screen(MessageScreen("[bold cyan]Emoji Verification[/bold cyan]\n\nNo unverified devices found.\n\n[dim]All known devices are already verified or\nthere are no other devices to verify.[/dim]"))
            return
        
        # Show device selection screen
        await self.show_device_selection_for_verification(unverified_devices)
    
    async def show_device_selection_for_verification(self, devices: List[Dict[str, Any]]):
        """Show device selection screen for verification.
        
        First shows user selection, then device selection for chosen user.
        """
        from textual.screen import Screen as BaseScreen
        
        # Group devices by user
        devices_by_user = {}
        for device_info in devices:
            user_id = device_info['user_id']
            if user_id not in devices_by_user:
                devices_by_user[user_id] = []
            devices_by_user[user_id].append(device_info)
        
        # If only one user, skip user selection
        if len(devices_by_user) == 1:
            user_id = list(devices_by_user.keys())[0]
            await self._show_user_devices_for_verification(user_id, devices_by_user[user_id])
            return
        
        # Show user selection screen first
        class UserSelectionScreen(BaseScreen):
            """Screen for selecting a user to verify."""
            
            BINDINGS = [
                Binding("escape", "app.pop_screen", "Back", priority=True),
            ]
            
            def __init__(self, parent_sessions_screen, devices_by_user, **kwargs):
                super().__init__(**kwargs)
                self.parent_sessions_screen = parent_sessions_screen
                self.devices_by_user = devices_by_user
            
            def compose(self) -> ComposeResult:
                yield Header()
                with ScrollableContainer():
                    yield Static("[bold cyan]Select User to Verify[/bold cyan]\n", id="title")
                    yield Static("[dim]Choose a user to see their unverified devices:[/dim]\n")
                    
                    for idx, (user_id, user_devices) in enumerate(self.devices_by_user.items()):
                        device_count = len(user_devices)
                        button_label = f"{user_id}\n[dim]{device_count} unverified device(s)[/dim]"
                        yield Button(button_label, id=f"user_{idx}")
                yield Footer()
            
            async def on_button_pressed(self, event: Button.Pressed) -> None:
                button_id = event.button.id
                if button_id.startswith("user_"):
                    idx = int(button_id.split("_")[1])
                    user_id = list(self.devices_by_user.keys())[idx]
                    user_devices = self.devices_by_user[user_id]
                    self.app.pop_screen()
                    await self.parent_sessions_screen._show_user_devices_for_verification(user_id, user_devices)
        
        self.app.push_screen(UserSelectionScreen(self, devices_by_user))
    
    async def _show_user_devices_for_verification(self, user_id: str, devices: List[Dict[str, Any]]):
        """Show device selection for a specific user."""
        from textual.screen import Screen as BaseScreen
        
        class DeviceSelectionScreen(BaseScreen):
            BINDINGS = [
                Binding("escape", "app.pop_screen", "Back", priority=True),
            ]
            
            def __init__(self, parent_sessions_screen, user_id: str, devices: List[Dict[str, Any]], **kwargs):
                super().__init__(**kwargs)
                self.parent_sessions_screen = parent_sessions_screen
                self.user_id = user_id
                self.devices = devices
            
            def compose(self) -> ComposeResult:
                yield Header()
                with ScrollableContainer():
                    yield Static(f"[bold cyan]Select Device to Verify[/bold cyan]\n", id="title")
                    yield Static(f"[bold]User:[/bold] {self.user_id}\n")
                    yield Static("[dim]Choose a device to start emoji verification:[/dim]\n")
                    
                    for idx, device_info in enumerate(self.devices):
                        device_id = device_info['device_id']
                        device_name = device_info['device_name']
                        
                        button_text = f"{device_name}\n[dim]{device_id}[/dim]"
                        yield Button(button_text, id=f"device_{idx}", variant="primary")
                yield Footer()
            
            async def on_button_pressed(self, event: Button.Pressed) -> None:
                button_id = event.button.id
                if button_id.startswith("device_"):
                    idx = int(button_id.split("_")[1])
                    device_info = self.devices[idx]
                    await self.start_verification(device_info)
            
            async def start_verification(self, device_info: Dict[str, Any]):
                """Start SAS verification with selected device."""
                from nio import ToDeviceError
                from nio.crypto import Sas, SasState
                
                try:
                    client = self.parent_sessions_screen.tui_app.bot.client
                    device = device_info['device']
                    
                    # Start key verification
                    resp = await client.start_key_verification(device)
                    
                    if isinstance(resp, ToDeviceError):
                        self.app.push_screen(MessageScreen(f"Failed to start verification: {resp.message}"))
                        return
                    
                    # Wait for the verification to be set up
                    await asyncio.sleep(1)
                    
                    # Get the SAS object from the client
                    sas = None
                    if hasattr(client, 'key_verifications'):
                        for transaction_id, verification in client.key_verifications.items():
                            if isinstance(verification, Sas):
                                if verification.other_olm_device == device:
                                    sas = verification
                                    break
                    
                    if not sas:
                        self.app.push_screen(MessageScreen("Verification started, but could not retrieve SAS object.\n\nPlease check the other device to continue."))
                        return
                    
                    # If we didn't start this verification (someone else initiated it), 
                    # we need to accept it and share our key first
                    if not sas.we_started_it and sas.state == SasState.created:
                        # Accept the verification request
                        await client.accept_key_verification(sas.transaction_id)
                        # Wait for state to update
                        await asyncio.sleep(0.5)
                    
                    # Wait for key exchange to complete (other device's key must be received)
                    max_wait = 10  # Maximum 10 seconds
                    wait_time = 0
                    while not sas.other_key_set and wait_time < max_wait:
                        await asyncio.sleep(0.5)
                        wait_time += 0.5
                    
                    if not sas.other_key_set:
                        self.app.push_screen(MessageScreen(
                            "Verification timeout: Did not receive the other device's key.\n\n"
                            "Please ensure the other device has accepted the verification request."
                        ))
                        return
                    
                    # Get emoji sequence
                    try:
                        emoji_list = sas.get_emoji()
                        emoji_display = " ".join([f"{emoji} ({desc})" for emoji, desc in emoji_list])
                    except Exception as e:
                        logger.error(f"Error getting emojis: {e}")
                        self.app.push_screen(MessageScreen(
                            f"Error getting emojis: {e}\n\n"
                            f"SAS state: {sas.state.name if hasattr(sas.state, 'name') else sas.state}\n"
                            f"Other key set: {sas.other_key_set}"
                        ))
                        return
                    
                    # Show verification screen with emojis
                    await self.show_verification_screen(sas, emoji_display, device_info)
                    
                except Exception as e:
                    logger.error(f"Error starting verification: {e}")
                    self.app.push_screen(MessageScreen(f"Error starting verification: {e}"))
            
            async def show_verification_screen(self, sas: Any, emoji_display: str, device_info: Dict[str, Any]):
                """Show the verification screen with emojis."""
                class VerificationScreen(ModalScreen):
                    BINDINGS = [
                        Binding("escape", "app.pop_screen", "Cancel", priority=True),
                    ]
                    
                    def __init__(self, device_selection_screen, sas, emoji_display: str, device_info: Dict[str, Any], **kwargs):
                        super().__init__(**kwargs)
                        self.device_selection_screen = device_selection_screen
                        self.sas = sas
                        self.emoji_display = emoji_display
                        self.device_info = device_info
                    
                    def compose(self) -> ComposeResult:
                        yield Header()
                        with Container():
                            yield Static("[bold cyan]Emoji Verification[/bold cyan]\n", id="title")
                            yield Static(f"[bold]Verifying device:[/bold]\n{self.device_info['user_id']}\n{self.device_info['device_name']}\n")
                            yield Static(f"[bold]Compare these emojis with the other device:[/bold]\n\n{self.emoji_display}\n")
                            yield Static("[bold]Do the emojis match?[/bold]\n")
                            yield Button("✅ Yes, they match", id="confirm", variant="success")
                            yield Button("❌ No, they don't match", id="reject", variant="error")
                        yield Footer()
                    
                    async def on_button_pressed(self, event: Button.Pressed) -> None:
                        if event.button.id == "confirm":
                            await self.confirm_verification()
                        elif event.button.id == "reject":
                            await self.reject_verification()
                    
                    async def confirm_verification(self):
                        """Confirm the SAS verification."""
                        from nio.crypto import SasState
                        
                        try:
                            # Check if we're in the right state
                            if not self.sas.other_key_set:
                                self.app.push_screen(MessageScreen(
                                    "Cannot confirm verification: Key exchange not complete.\n\n"
                                    "The other device has not sent its key yet. Please wait or try again."
                                ))
                                return
                            
                            # Accept the SAS
                            self.sas.accept_sas()
                            
                            # Send the MAC
                            client = self.device_selection_screen.parent_sessions_screen.tui_app.bot.client
                            await client.send_to_device_messages()
                            
                            self.app.push_screen(MessageScreen("✅ Verification successful!\n\nThe device has been verified and marked as trusted."))
                            self.dismiss()
                            
                        except Exception as e:
                            logger.error(f"Error confirming verification: {e}")
                            self.app.push_screen(MessageScreen(
                                f"Error confirming verification: {e}\n\n"
                                f"SAS state: {self.sas.state.name if hasattr(self.sas.state, 'name') else self.sas.state}\n"
                                f"Other key set: {self.sas.other_key_set}"
                            ))
                    
                    async def reject_verification(self):
                        """Reject the SAS verification."""
                        from nio.crypto import SasState
                        
                        try:
                            # Check if we're in the right state
                            if not self.sas.other_key_set:
                                self.app.push_screen(MessageScreen(
                                    "Cannot reject verification: Key exchange not complete.\n\n"
                                    "The other device has not sent its key yet. Please wait or try again."
                                ))
                                return
                            
                            self.sas.reject_sas()
                            
                            client = self.device_selection_screen.parent_sessions_screen.tui_app.bot.client
                            await client.send_to_device_messages()
                            
                            self.app.push_screen(MessageScreen("❌ Verification rejected.\n\nThe emojis did not match. The device was not verified."))
                            self.dismiss()
                            
                        except Exception as e:
                            logger.error(f"Error rejecting verification: {e}")
                            self.app.push_screen(MessageScreen(
                                f"Error rejecting verification: {e}\n\n"
                                f"SAS state: {self.sas.state.name if hasattr(self.sas.state, 'name') else self.sas.state}\n"
                                f"Other key set: {self.sas.other_key_set}"
                            ))
                
                self.app.push_screen(VerificationScreen(self, sas, emoji_display, device_info))
        
        self.app.push_screen(DeviceSelectionScreen(self, user_id, devices))
    
    async def show_qr_verification(self):
        """Show QR code for device verification."""
        if not self.tui_app.bot or not self.tui_app.bot.client or not self.tui_app.bot.client.olm:
            self.app.push_screen(MessageScreen("Encryption is not enabled. Cannot generate QR code."))
            return
        
        try:
            # Generate verification data
            device_id = self.tui_app.bot.client.device_id or "Unknown"
            user_id = self.tui_app.bot.client.user_id or "Unknown"
            
            # Create QR code data
            qr_data = {
                'user_id': user_id,
                'device_id': device_id,
                'verification': 'device_verification',
                'timestamp': int(time.time())
            }
            
            qr_string = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Convert to ASCII art
            qr_ascii = ""
            matrix = qr.get_matrix()
            for row in matrix:
                qr_ascii += "".join(["██" if cell else "  " for cell in row]) + "\n"
            
            message = f"""[bold cyan]QR Code Verification[/bold cyan]

Scan this QR code with the other device:

{qr_ascii}

Device: {device_id}
User: {user_id}

[dim]Note: The other device needs to scan this QR code
to verify this bot's identity.[/dim]"""
            
            self.app.push_screen(MessageScreen(message))
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            self.app.push_screen(MessageScreen(f"Error generating QR code: {e}"))
    
    async def show_device_fingerprint(self):
        """Show device fingerprint for manual verification."""
        if not self.tui_app.bot or not self.tui_app.bot.client or not self.tui_app.bot.client.olm:
            self.app.push_screen(MessageScreen("Encryption is not enabled."))
            return
        
        try:
            device_id = self.tui_app.bot.client.device_id or "Unknown"
            user_id = self.tui_app.bot.client.user_id or "Unknown"
            
            # Get fingerprint key if available
            fingerprint = "Not available"
            if hasattr(self.tui_app.bot.client, 'olm') and self.tui_app.bot.client.olm:
                if hasattr(self.tui_app.bot.client.olm, 'account'):
                    identity_keys = self.tui_app.bot.client.olm.account.identity_keys
                    ed25519_key = identity_keys.get('ed25519', 'Unknown')
                    # Format as fingerprint (groups of 4)
                    fingerprint = ' '.join([ed25519_key[i:i+4] for i in range(0, len(ed25519_key), 4)])
            
            message = f"""[bold cyan]Device Fingerprint[/bold cyan]

[bold]User ID:[/bold] {user_id}
[bold]Device ID:[/bold] {device_id}

[bold]Ed25519 Fingerprint:[/bold]
{fingerprint}

[dim]Share this fingerprint with the other party
to verify your device identity manually.[/dim]"""
            
            self.app.push_screen(MessageScreen(message))
            
        except Exception as e:
            logger.error(f"Error getting fingerprint: {e}")
            self.app.push_screen(MessageScreen(f"Error getting fingerprint: {e}"))
    
    async def reset_olm_sessions(self):
        """Reset Olm encryption sessions."""
        message = """[bold yellow]⚠️  Reset Olm Sessions[/bold yellow]

This will delete all encryption sessions and keys.
You will need to re-verify devices after reset.

[bold red]This action cannot be undone![/bold red]

[dim]To reset Olm sessions:
1. Stop the bot
2. Delete the store directory (default: ./store)
3. Restart the bot
4. Re-verify devices[/dim]"""
        
        self.app.push_screen(MessageScreen(message))


class SayScreen(Screen):
    """Screen to send messages to rooms."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, tui_app, rooms: List[Dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
        self.rooms = rooms
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Send Message[/bold cyan]\n", id="title")
            if self.rooms:
                room_options = [(room['name'], room['id']) for room in self.rooms]
                yield Label("Select Room:")
                yield Select(room_options, prompt="Choose a room", id="room_select")
                yield Label("\nMessage:")
                yield Input(placeholder="Type your message here...", id="message_input")
                yield Button("Send", id="send_button", variant="primary")
            else:
                yield Static("[yellow]No rooms available[/yellow]")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send_button":
            room_select = self.query_one("#room_select", Select)
            message_input = self.query_one("#message_input", Input)
            
            if room_select.value and message_input.value:
                try:
                    await self.tui_app.send_message_to_room(str(room_select.value), message_input.value)
                    self.app.push_screen(MessageScreen(f"Message sent to {room_select.value}!"))
                    message_input.value = ""
                except Exception as e:
                    self.app.push_screen(MessageScreen(f"Error sending message: {e}"))
            else:
                self.app.push_screen(MessageScreen("Please select a room and enter a message"))


class LogScreen(Screen):
    """Screen to display logs."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, log_content: str, **kwargs):
        super().__init__(**kwargs)
        self.log_content = log_content
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Log View[/bold cyan]\n", id="title")
            yield TextArea(self.log_content, read_only=True, id="log_area")
        yield Footer()


class ConfigEditScreen(ModalScreen):
    """Modal screen for editing a configuration value."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel", priority=True),
    ]
    
    def __init__(self, config_key: str, current_value: Any, value_type: str, **kwargs):
        super().__init__(**kwargs)
        self.config_key = config_key
        self.current_value = current_value
        self.value_type = value_type
        self.new_value = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static(f"[bold cyan]Edit Configuration[/bold cyan]\n", id="title")
            yield Static(f"[bold]Key:[/bold] {self.config_key}")
            yield Static(f"[bold]Type:[/bold] {self.value_type}")
            yield Static(f"[bold]Current Value:[/bold] {self.current_value}\n")
            
            if self.value_type == "boolean":
                yield Label("New Value:")
                yield Switch(value=bool(self.current_value), id="value_switch")
            else:
                yield Label("New Value:")
                yield Input(placeholder=str(self.current_value), id="value_input", value=str(self.current_value))
            
            yield Button("Save", id="save_button", variant="primary")
            yield Button("Cancel", id="cancel_button")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_button":
            if self.value_type == "boolean":
                switch = self.query_one("#value_switch", Switch)
                self.new_value = switch.value
            else:
                input_widget = self.query_one("#value_input", Input)
                value_str = input_widget.value
                
                # Convert based on type
                try:
                    if self.value_type == "integer":
                        self.new_value = int(value_str)
                    elif self.value_type == "float":
                        self.new_value = float(value_str)
                    elif self.value_type == "list":
                        # Parse as JSON array
                        self.new_value = json.loads(value_str) if value_str.startswith('[') else value_str.split(',')
                    else:
                        self.new_value = value_str
                except (ValueError, json.JSONDecodeError) as e:
                    self.app.push_screen(MessageScreen(f"Invalid value format: {e}"))
                    return
            
            self.dismiss(self.new_value)
        elif event.button.id == "cancel_button":
            self.dismiss(None)


class SetScreen(Screen):
    """Screen to change operational variables."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
        Binding("a", "apply", "Apply"),
        Binding("s", "save", "Save"),
        Binding("d", "discard", "Discard"),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
        self.pending_changes = {}
    
    def _get_setting_label(self, config_key: str) -> str:
        """Generate a label for a setting showing current and default values.
        
        Args:
            config_key: Configuration key (e.g., 'bot.command_prefix')
            
        Returns:
            Formatted label with current and default values
        """
        current_value = self.tui_app.config.get(config_key, "")
        
        # Get default value
        default_config = self.tui_app.config._get_default_config()
        keys = config_key.split('.')
        default_value = default_config
        for key in keys:
            if isinstance(default_value, dict):
                default_value = default_value.get(key, "")
            else:
                default_value = ""
                break
        
        # Format values for display
        def format_value(val):
            if isinstance(val, bool):
                return str(val)
            elif isinstance(val, list):
                return f"[{len(val)} items]" if val else "[]"
            elif isinstance(val, str):
                if any(sensitive in config_key.lower() for sensitive in ['password', 'token', 'secret']):
                    return "***" if val else "(empty)"
                return val if len(str(val)) <= 30 else f"{str(val)[:27]}..."
            else:
                return str(val)
        
        current_display = format_value(current_value)
        default_display = format_value(default_value)
        
        # Determine if value is modified (use color if available)
        is_modified = current_value != default_value
        if is_modified and self.tui_app.use_color:
            # Use yellow to indicate modified from default
            return f"{config_key}\n[yellow]Current:[/yellow] {current_display} [dim]| Default: {default_display}[/dim]"
        else:
            return f"{config_key}\nCurrent: {current_display} | Default: {default_display}"
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with ScrollableContainer():
            yield Static("[bold cyan]Set Operational Variables[/bold cyan]\n", id="title")
            yield Static("[dim]Select a variable to edit. Modified values shown in color.[/dim]\n")
            
            # Matrix configuration options
            yield Static("[bold]Matrix Configuration:[/bold]")
            yield Button(self._get_setting_label("matrix.homeserver"), id="edit_matrix_homeserver")
            yield Button(self._get_setting_label("matrix.user_id"), id="edit_matrix_user_id")
            yield Button(self._get_setting_label("matrix.device_id"), id="edit_matrix_device_id")
            yield Button(self._get_setting_label("matrix.device_name"), id="edit_matrix_device_name")
            yield Button(self._get_setting_label("matrix.auth_type"), id="edit_matrix_auth_type")
            yield Button(self._get_setting_label("matrix.password"), id="edit_matrix_password")
            yield Button(self._get_setting_label("matrix.access_token"), id="edit_matrix_access_token")
            yield Button(self._get_setting_label("matrix.store_path"), id="edit_matrix_store_path")
            
            # Semaphore configuration options
            yield Static("\n[bold]Semaphore Configuration:[/bold]")
            yield Button(self._get_setting_label("semaphore.url"), id="edit_semaphore_url")
            yield Button(self._get_setting_label("semaphore.api_token"), id="edit_semaphore_api_token")
            yield Button(self._get_setting_label("semaphore.ssl_verify"), id="edit_semaphore_ssl_verify")
            
            # Bot configuration options
            yield Static("\n[bold]Bot Configuration:[/bold]")
            yield Button(self._get_setting_label("bot.command_prefix"), id="edit_bot_command_prefix")
            yield Button(self._get_setting_label("bot.allowed_rooms"), id="edit_bot_allowed_rooms")
            yield Button(self._get_setting_label("bot.admin_users"), id="edit_bot_admin_users")
            yield Button(self._get_setting_label("bot.greetings_enabled"), id="edit_bot_greetings_enabled")
            yield Button(self._get_setting_label("bot.greeting_rooms"), id="edit_bot_greeting_rooms")
            yield Button(self._get_setting_label("bot.startup_message"), id="edit_bot_startup_message")
            yield Button(self._get_setting_label("bot.shutdown_message"), id="edit_bot_shutdown_message")
            yield Button(self._get_setting_label("bot.log_file"), id="edit_bot_log_file")
            
            yield Static("\n[bold]Actions:[/bold]")
            yield Button("Apply Changes (Runtime Only)", id="apply_button", variant="primary")
            yield Button("Save to config.json", id="save_button", variant="success")
            yield Button("Discard Changes", id="discard_button", variant="warning")
            
            if self.pending_changes:
                yield Static(f"\n[bold yellow]Pending Changes:[/bold yellow]")
                for key, value in self.pending_changes.items():
                    # Redact sensitive values in display
                    display_value = value
                    if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret']):
                        display_value = '***REDACTED***'
                    yield Static(f"  • {key} = {display_value}")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id.startswith("edit_"):
            # Remove "edit_" prefix and convert underscores back to dots for config key
            config_key = button_id[5:].replace('_', '.')
            await self.edit_config_value(config_key)
        elif button_id == "apply_button":
            await self.apply_changes()
        elif button_id == "save_button":
            await self.save_changes()
        elif button_id == "discard_button":
            await self.discard_changes()
    
    async def action_apply(self):
        """Handle apply action."""
        await self.apply_changes()
    
    async def action_save(self):
        """Handle save action."""
        await self.save_changes()
    
    async def action_discard(self):
        """Handle discard action."""
        await self.discard_changes()
    
    async def discard_changes(self):
        """Discard all pending changes."""
        self.pending_changes = {}
        self.app.push_screen(MessageScreen("Changes discarded."))
        self.refresh()
    
    async def edit_config_value(self, config_key: str):
        """Edit a configuration value."""
        # Get current value using dot notation
        current_value = self.tui_app.config.get(config_key, "")
        
        # Determine value type
        if isinstance(current_value, bool):
            value_type = "boolean"
        elif isinstance(current_value, int):
            value_type = "integer"
        elif isinstance(current_value, float):
            value_type = "float"
        elif isinstance(current_value, list):
            value_type = "list"
            current_value = json.dumps(current_value)
        else:
            value_type = "string"
        
        # Show edit screen
        def handle_result(new_value):
            if new_value is not None:
                self.pending_changes[config_key] = new_value
                # Redact sensitive values in display
                display_value = new_value
                if any(sensitive in config_key.lower() for sensitive in ['password', 'token', 'secret']):
                    display_value = '***REDACTED***'
                self.app.push_screen(MessageScreen(f"Changed {config_key} to: {display_value}\n\nRemember to Apply or Save changes!"))
                self.refresh()
        
        await self.app.push_screen(ConfigEditScreen(config_key, current_value, value_type), handle_result)
    
    async def apply_changes(self):
        """Apply changes to runtime configuration only."""
        if not self.pending_changes:
            self.app.push_screen(MessageScreen("No pending changes to apply."))
            return
        
        # Update runtime configuration
        for key, value in self.pending_changes.items():
            self._set_nested_value(self.tui_app.config.config, key, value)
        
        self.app.push_screen(MessageScreen(f"Applied {len(self.pending_changes)} changes to runtime configuration.\n\nChanges will be lost when the bot restarts unless saved to config.json."))
        self.pending_changes = {}
        self.refresh()
    
    def _set_nested_value(self, config_dict: dict, key: str, value: Any):
        """Set a value in nested dictionary using dot notation.
        
        Args:
            config_dict: Configuration dictionary
            key: Dot-separated key path (e.g., 'matrix.homeserver')
            value: Value to set
        """
        keys = key.split('.')
        current = config_dict
        
        # Navigate to the nested location
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
    
    async def save_changes(self):
        """Save changes to config.json file."""
        if not self.pending_changes:
            self.app.push_screen(MessageScreen("No pending changes to save."))
            return
        
        try:
            # Update configuration
            for key, value in self.pending_changes.items():
                self._set_nested_value(self.tui_app.config.config, key, value)
            
            # Save to file
            config_file = getattr(self.tui_app.config, 'config_file', 'config.json')
            with open(config_file, 'w') as f:
                json.dump(self.tui_app.config.config, f, indent=2)
            
            self.app.push_screen(MessageScreen(f"Saved {len(self.pending_changes)} changes to {config_file}.\n\nChanges are now persistent and will survive restarts."))
            self.pending_changes = {}
            self.refresh()
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            self.app.push_screen(MessageScreen(f"Error saving configuration: {e}"))


class ShowScreen(Screen):
    """Screen to show current configuration."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("b", "app.pop_screen", "Back"),
    ]
    
    def __init__(self, config_text: str, **kwargs):
        super().__init__(**kwargs)
        self.config_text = config_text
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Current Configuration[/bold cyan]\n", id="title")
            yield TextArea(self.config_text, read_only=True, id="config_area")
        yield Footer()


class OIDCAuthScreen(ModalScreen):
    """Screen for OIDC authentication token input."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Cancel", priority=True),
    ]
    
    def __init__(self, sso_url: str, redirect_url: str, identity_providers: list, **kwargs):
        super().__init__(**kwargs)
        self.sso_url = sso_url
        self.redirect_url = redirect_url
        self.identity_providers = identity_providers
        self.token = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        from textual.widgets import Markdown
        
        yield Header()
        with ScrollableContainer():
            yield Static("[bold cyan]OIDC/SSO Authentication Required[/bold cyan]\n", id="title")
            
            yield Static("[bold yellow]Step 1:[/bold yellow] [bold]Copy and open this URL in your browser:[/bold]\n")
            # Use TextArea with read_only=True to allow text selection in terminals
            yield TextArea(self.sso_url, read_only=True, id="sso_url")
            yield Static("[dim]↑ Select and copy the URL above (you can use your mouse or keyboard)[/dim]\n")
            
            if self.identity_providers:
                yield Static(f"[bold]Available Identity Providers:[/bold]")
                for idp in self.identity_providers:
                    provider_name = idp.get('name', idp.get('id', 'Unknown'))
                    yield Static(f"  • {provider_name}")
                yield Static("")
            
            yield Static(f"[bold yellow]Step 2:[/bold yellow] [bold]After browser authentication, you'll be redirected to:[/bold]")
            yield Static(f"  {self.redirect_url}")
            yield Static("[dim]The redirect URL will contain a 'loginToken' parameter[/dim]\n")
            
            yield Static("[bold yellow]Step 3:[/bold yellow] [bold]Paste the callback URL or just the token in the field below:[/bold]")
            yield Static("[dim]You can paste either the full URL or just the token value[/dim]")
            yield Input(
                placeholder="Paste here: https://example.com/callback?loginToken=... or just the token", 
                id="token_input"
            )
            yield Static("")
            
            yield Button("Submit Token", id="submit_button", variant="primary")
            yield Button("Cancel", id="cancel_button")
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit_button":
            input_widget = self.query_one("#token_input", Input)
            token_input = input_widget.value.strip()
            
            if not token_input:
                self.app.push_screen(MessageScreen("Please enter the callback URL or login token"))
                return
            
            # Extract token if full URL was provided
            if 'loginToken=' in token_input:
                import urllib.parse
                parsed = urllib.parse.urlparse(token_input)
                params = urllib.parse.parse_qs(parsed.query)
                if 'loginToken' in params:
                    self.token = params['loginToken'][0]
                else:
                    # Try fragment as some SSO providers use fragments
                    params = urllib.parse.parse_qs(parsed.fragment)
                    if 'loginToken' in params:
                        self.token = params['loginToken'][0]
                    else:
                        self.app.push_screen(MessageScreen("Could not find loginToken in provided URL"))
                        return
            else:
                # Assume the input is just the token
                self.token = token_input
            
            self.dismiss(self.token)
        elif event.button.id == "cancel_button":
            self.dismiss(None)


class MessageScreen(Screen):
    """Simple message display screen."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("enter", "app.pop_screen", "OK", priority=True),
    ]
    
    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static(self.message)
            yield Button("OK", id="ok_button")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "ok_button":
            self.app.pop_screen()


class ChatrixTUI(App):
    """ChatrixCD Text User Interface."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: #4A9B7F;
        color: white;
    }
    
    Footer {
        background: #2D3238;
    }
    
    Button {
        margin: 1;
        min-width: 20;
    }
    
    Button.primary {
        background: #4A9B7F;
    }
    
    Static#title {
        text-align: center;
        padding: 1;
    }
    
    Container {
        height: 100%;
        padding: 1;
    }
    
    ListView {
        height: auto;
    }
    
    Select {
        margin: 1;
    }
    
    Input {
        margin: 1;
    }
    
    TextArea {
        height: 80%;
        margin: 1;
    }
    """
    
    TITLE = "ChatrixCD"
    SUB_TITLE = "Matrix CI/CD Bot - Interactive Interface"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("s", "show_status", "Status"),
        Binding("a", "show_admins", "Admins"),
        Binding("r", "show_rooms", "Rooms"),
        Binding("e", "show_sessions", "Sessions"),
        Binding("m", "show_say", "Say"),
        Binding("l", "show_log", "Log"),
        Binding("t", "show_set", "Set"),
        Binding("c", "show_config", "Show Config"),
        Binding("x", "show_aliases", "Aliases"),
    ]
    
    def __init__(self, bot, config, use_color: bool = True, **kwargs):
        """Initialize the TUI.
        
        Args:
            bot: The ChatrixBot instance
            config: Configuration object
            use_color: Whether to use colors
        """
        super().__init__(**kwargs)
        self.bot = bot
        self.config = config
        self.use_color = use_color
        self.start_time = time.time()
        self.messages_processed = 0
        self.errors = 0
        self.warnings = 0
        self.login_task = None  # Will be set by run_tui_with_bot if login is needed
        self.bot_task = None  # Will store the sync task
        self.pending_verifications_count = 0  # Track pending verification requests
        self.last_notified_verifications = set()  # Track which verifications we've notified about
        
    def compose(self) -> ComposeResult:
        """Create child widgets for main menu."""
        yield Header()
        with ScrollableContainer():
            yield Static("[bold cyan]ChatrixCD[/bold cyan]", id="title")
            yield Static("[dim]Matrix CI/CD Bot - Interactive Interface[/dim]\n")
            
            # Add active tasks widget
            tasks_widget = ActiveTasksWidget(id="active_tasks")
            yield tasks_widget
            yield Static("\n")
            
            yield Button("STATUS - Show bot status [s]", id="status")
            yield Button("ADMINS - View admin users [a]", id="admins")
            yield Button("ROOMS - Show joined rooms [r]", id="rooms")
            yield Button("SESSIONS - Session management [e]", id="sessions")
            yield Button("SAY - Send message to room [m]", id="say")
            yield Button("LOG - View log [l]", id="log")
            yield Button("SET - Change operational variables [t]", id="set")
            yield Button("SHOW - Show current configuration [c]", id="show")
            yield Button("ALIASES - Manage command aliases [x]", id="aliases")
            yield Button("QUIT - Exit [q]", id="quit", variant="error")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when the TUI is mounted."""
        # Start background task to update active tasks
        self.set_interval(5, self.update_active_tasks)
        
        # Start background task to check for pending verifications
        self.set_interval(3, self.check_pending_verifications)
        
        # If login task is set, perform login after TUI has started
        # This is necessary for OIDC flow which needs to push screens to the TUI
        if self.login_task:
            logger.debug("TUI mounted, starting login task")
            asyncio.create_task(self.login_task())
    
    async def update_active_tasks(self):
        """Update the active tasks widget."""
        try:
            if self.bot and hasattr(self.bot, 'command_handler'):
                active_tasks = self.bot.command_handler.active_tasks
                
                # Convert to list format for widget
                tasks_list = []
                for task_id, task_info in active_tasks.items():
                    # Get current status from Semaphore if possible
                    project_id = task_info.get('project_id')
                    try:
                        task_status = await self.bot.semaphore.get_task_status(project_id, task_id)
                        status = task_status.get('status', 'unknown') if task_status else 'unknown'
                    except Exception:
                        status = 'unknown'
                    
                    tasks_list.append({
                        'task_id': task_id,
                        'project_id': project_id,
                        'status': status
                    })
                
                # Update widget
                widget = self.query_one("#active_tasks", ActiveTasksWidget)
                widget.tasks = tasks_list
        except Exception as e:
            logger.debug(f"Error updating active tasks: {e}")
    
    async def check_pending_verifications(self):
        """Check for pending verification requests and notify user."""
        try:
            if not self.bot or not self.bot.client or not self.bot.client.olm:
                return
            
            client = self.bot.client
            current_verifications = set()
            
            # Check for active key verifications
            if hasattr(client, 'key_verifications') and client.key_verifications:
                for transaction_id, verification in client.key_verifications.items():
                    current_verifications.add(transaction_id)
                    
                    # Check if this is a new verification request
                    if transaction_id not in self.last_notified_verifications:
                        user_id = getattr(verification, 'user_id', 'Unknown')
                        device_id = getattr(verification, 'device_id', 'Unknown')
                        
                        # Show notification
                        logger.info(
                            f"New verification request from {user_id} (device: {device_id}). "
                            "Check Sessions menu to verify."
                        )
                        
                        # Create notification message
                        notification = (
                            f"🔔 [bold yellow]New Verification Request[/bold yellow]\n\n"
                            f"From: {user_id}\n"
                            f"Device: {device_id}\n\n"
                            f"[dim]Go to Sessions (press 'e') > View Pending Verification Requests[/dim]"
                        )
                        
                        # Show notification as a temporary screen
                        self.notify(
                            f"New verification request from {user_id}",
                            severity="information",
                            timeout=10
                        )
            
            # Update tracking sets
            self.last_notified_verifications = current_verifications
            self.pending_verifications_count = len(current_verifications)
            
        except Exception as e:
            logger.debug(f"Error checking pending verifications: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "status":
            await self.show_status()
        elif button_id == "admins":
            await self.show_admins()
        elif button_id == "rooms":
            await self.show_rooms()
        elif button_id == "sessions":
            await self.show_sessions()
        elif button_id == "say":
            await self.show_say()
        elif button_id == "log":
            await self.show_log()
        elif button_id == "set":
            await self.show_set()
        elif button_id == "show":
            await self.show_config()
        elif button_id == "aliases":
            await self.show_aliases()
        elif button_id == "quit":
            await self.action_quit()
    
    async def show_status(self):
        """Show bot status screen."""
        # Create status screen
        from textual.screen import Screen
        
        class StatusScreen(Screen):
            BINDINGS = [
                Binding("escape", "app.pop_screen", "Back", priority=True),
            ]
            
            def __init__(self, tui_app, **kwargs):
                super().__init__(**kwargs)
                self.tui_app = tui_app
            
            def compose(self) -> ComposeResult:
                yield Header()
                with Container():
                    status_widget = BotStatusWidget()
                    # Update status
                    if self.tui_app.bot and self.tui_app.bot.client:
                        status_widget.matrix_status = "Connected" if self.tui_app.bot.client.logged_in else "Disconnected"
                    else:
                        status_widget.matrix_status = "Not initialized"
                    
                    status_widget.semaphore_status = "Connected" if self.tui_app.bot and self.tui_app.bot.semaphore else "Unknown"
                    
                    # Calculate uptime
                    uptime_seconds = int(time.time() - self.tui_app.start_time)
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    status_widget.uptime = f"{hours}h {minutes}m {seconds}s"
                    
                    status_widget.messages_processed = self.tui_app.messages_processed
                    status_widget.errors = self.tui_app.errors
                    status_widget.warnings = self.tui_app.warnings
                    
                    yield status_widget
                yield Footer()
        
        self.push_screen(StatusScreen(self))
    
    async def show_admins(self):
        """Show admin users screen."""
        bot_config = self.config.get_bot_config()
        admins = bot_config.get('admin_users', [])
        self.push_screen(AdminsScreen(admins))
    
    async def show_rooms(self):
        """Show rooms screen."""
        rooms = []
        if self.bot and self.bot.client and self.bot.client.rooms:
            for room_id, room in self.bot.client.rooms.items():
                rooms.append({
                    'id': room_id,
                    'name': room.display_name or room_id
                })
        self.push_screen(RoomsScreen(rooms))
    
    async def show_sessions(self):
        """Show session management screen."""
        self.push_screen(SessionsScreen(self))
    
    async def show_say(self):
        """Show message sending screen."""
        rooms = []
        if self.bot and self.bot.client and self.bot.client.rooms:
            for room_id, room in self.bot.client.rooms.items():
                rooms.append({
                    'id': room_id,
                    'name': room.display_name or room_id
                })
        self.push_screen(SayScreen(self, rooms))
    
    async def show_log(self):
        """Show log screen."""
        log_content = ""
        log_file = self.config.get('bot.log_file', 'chatrixcd.log')
        try:
            with open(log_file, 'r') as f:
                # Read last 1000 lines and reverse order (most recent first)
                lines = f.readlines()
                reversed_lines = lines[-1000:]
                reversed_lines.reverse()
                log_content = ''.join(reversed_lines)
        except FileNotFoundError:
            log_content = f"Log file not found: {log_file}"
        except Exception as e:
            log_content = f"Error reading log: {e}"
        
        self.push_screen(LogScreen(log_content))
    
    async def show_set(self):
        """Show settings screen."""
        self.push_screen(SetScreen(self))
    
    async def show_config(self):
        """Show configuration screen."""
        import json
        import copy
        from chatrixcd.redactor import SensitiveInfoRedactor
        
        # Deep copy config to avoid modifying original
        config_dict = copy.deepcopy(self.config.config)
        
        # Redact sensitive fields
        sensitive_fields = ['password', 'access_token', 'api_token', 'client_secret', 'oidc_client_secret']
        
        def redact_sensitive(obj):
            """Recursively redact sensitive fields."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in sensitive_fields and value:
                        obj[key] = '***REDACTED***'
                    else:
                        redact_sensitive(value)
            elif isinstance(obj, list):
                for item in obj:
                    redact_sensitive(item)
        
        redact_sensitive(config_dict)
        config_text = json.dumps(config_dict, indent=2)
        
        self.push_screen(ShowScreen(config_text))
    
    async def show_aliases(self):
        """Show aliases management screen."""
        self.push_screen(AliasesScreen(self))
    
    async def send_message_to_room(self, room_id: str, message: str):
        """Send a message to a room.
        
        Args:
            room_id: The room ID to send to
            message: The message to send
        """
        if self.bot:
            await self.bot.send_message(room_id, message)
            self.messages_processed += 1
    
    async def action_quit(self):
        """Handle quit action."""
        self.exit()
    
    async def action_show_status(self):
        """Handle status action."""
        await self.show_status()
    
    async def action_show_admins(self):
        """Handle admins action."""
        await self.show_admins()
    
    async def action_show_rooms(self):
        """Handle rooms action."""
        await self.show_rooms()
    
    async def action_show_sessions(self):
        """Handle sessions action."""
        await self.show_sessions()
    
    async def action_show_say(self):
        """Handle say action."""
        await self.show_say()
    
    async def action_show_log(self):
        """Handle log action."""
        await self.show_log()
    
    async def action_show_set(self):
        """Handle set action."""
        await self.show_set()
    
    async def action_show_config(self):
        """Handle show config action."""
        await self.show_config()
    
    async def action_show_aliases(self):
        """Handle show aliases action."""
        await self.show_aliases()


async def run_tui(bot, config, use_color: bool = True, mouse: bool = False):
    """Run the TUI interface.
    
    Args:
        bot: The ChatrixBot instance
        config: Configuration object
        use_color: Whether to use colors
        mouse: Whether to enable mouse support (default: False)
    """
    app = ChatrixTUI(bot, config, use_color=use_color)
    await app.run_async(mouse=mouse)


async def show_config_tui(config):
    """Show configuration in a TUI window.
    
    Args:
        config: Configuration object
    """
    import json
    import copy
    from chatrixcd.redactor import SensitiveInfoRedactor
    
    # Deep copy config to avoid modifying original
    config_dict = copy.deepcopy(config.config)
    
    # Redact sensitive fields
    sensitive_fields = ['password', 'access_token', 'api_token', 'client_secret', 'oidc_client_secret']
    
    def redact_sensitive(obj):
        """Recursively redact sensitive fields."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in sensitive_fields and value:
                    obj[key] = '***REDACTED***'
                else:
                    redact_sensitive(value)
        elif isinstance(obj, list):
            for item in obj:
                redact_sensitive(item)
    
    redact_sensitive(config_dict)
    config_text = json.dumps(config_dict, indent=2)
    
    # Create a simple TUI app to display the config
    class ConfigViewerApp(App):
        """Simple app to view configuration."""
        
        CSS = """
        Screen {
            background: $surface;
        }
        
        Header {
            background: #4A9B7F;
            color: white;
        }
        
        Footer {
            background: #2D3238;
        }
        
        Container {
            height: 100%;
            padding: 1;
        }
        
        TextArea {
            height: 90%;
            margin: 1;
        }
        """
        
        TITLE = "ChatrixCD Configuration"
        SUB_TITLE = "Press 'q' or ESC to exit"
        
        BINDINGS = [
            Binding("q", "quit", "Quit", priority=True),
            Binding("escape", "quit", "Quit", priority=True),
        ]
        
        def __init__(self, config_text: str, **kwargs):
            super().__init__(**kwargs)
            self.config_text = config_text
        
        def compose(self) -> ComposeResult:
            """Create child widgets."""
            yield Header()
            with Container():
                yield Static("[bold cyan]Configuration[/bold cyan]\n", id="title")
                yield TextArea(self.config_text, read_only=True, id="config_area")
            yield Footer()
        
        async def action_quit(self):
            """Handle quit action."""
            self.exit()
    
    app = ConfigViewerApp(config_text)
    await app.run_async()
