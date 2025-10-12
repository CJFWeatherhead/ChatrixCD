"""Text User Interface for ChatrixCD bot."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label, Input, Select, TextArea
from textual.screen import Screen
from textual.binding import Binding
from textual import events
from textual.reactive import reactive

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


class AdminsScreen(Screen):
    """Screen to display admin users."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]
    
    def __init__(self, admins: List[str], **kwargs):
        super().__init__(**kwargs)
        self.admins = admins
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Admin Users[/bold cyan]\n", id="title")
            if self.admins:
                for admin in self.admins:
                    yield Static(f"  • {admin}")
            else:
                yield Static("[yellow]No admin users configured[/yellow]")
        yield Footer()


class RoomsScreen(Screen):
    """Screen to display rooms the bot is in."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
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
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Session Management[/bold cyan]\n", id="title")
            yield Button("View Sessions", id="view_sessions")
            yield Button("Reset Olm Sessions", id="reset_olm")
            yield Static("\n[dim]Session verification features coming soon...[/dim]")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "view_sessions":
            self.app.push_screen(MessageScreen("Session list feature coming soon..."))
        elif event.button.id == "reset_olm":
            self.app.push_screen(MessageScreen("Olm reset feature coming soon..."))


class SayScreen(Screen):
    """Screen to send messages to rooms."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
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


class SetScreen(Screen):
    """Screen to change operational variables."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container():
            yield Static("[bold cyan]Set Operational Variables[/bold cyan]\n", id="title")
            yield Static("[dim]Configuration editing coming soon...[/dim]")
            yield Button("Back", id="back_button")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back_button":
            self.app.pop_screen()


class ShowScreen(Screen):
    """Screen to show current configuration."""
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
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
        
    def compose(self) -> ComposeResult:
        """Create child widgets for main menu."""
        yield Header()
        with Container():
            yield Static("[bold cyan]ChatrixCD[/bold cyan]", id="title")
            yield Static("[dim]Matrix CI/CD Bot - Interactive Interface[/dim]\n")
            yield Button("STATUS - Show bot status", id="status")
            yield Button("ADMINS - View admin users", id="admins")
            yield Button("ROOMS - Show joined rooms", id="rooms")
            yield Button("SESSIONS - Session management", id="sessions")
            yield Button("SAY - Send message to room", id="say")
            yield Button("LOG - View log", id="log")
            yield Button("SET - Change operational variables", id="set")
            yield Button("SHOW - Show current configuration", id="show")
            yield Button("QUIT - Exit", id="quit", variant="error")
        yield Footer()
    
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
        try:
            with open('chatrixcd.log', 'r') as f:
                # Read last 1000 lines
                lines = f.readlines()
                log_content = ''.join(lines[-1000:])
        except FileNotFoundError:
            log_content = "Log file not found"
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


async def run_tui(bot, config, use_color: bool = True):
    """Run the TUI interface.
    
    Args:
        bot: The ChatrixBot instance
        config: Configuration object
        use_color: Whether to use colors
    """
    app = ChatrixTUI(bot, config, use_color=use_color)
    await app.run_async()
