"""Turbo Vision-style Text User Interface for ChatrixCD bot.

This TUI implementation provides a classic Turbo Vision aesthetic with:
- Menu bar at the top (File, Edit, Run, Help)
- 3D windowed appearance with shadows
- Status bar at the bottom showing task status
- Chatrix brand colors (#4A9B7F green)
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
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer, VerticalScroll
from textual.widgets import (
    Header, Footer, Static, Button, ListView, ListItem, Label, 
    Input, Select, TextArea, DataTable, Switch, OptionList
)
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import events
from textual.reactive import reactive
from chatrixcd.verification import DeviceVerificationManager
from nio.crypto import Sas

logger = logging.getLogger(__name__)


class TurboMenuBar(Static):
    """Turbo Vision-style menu bar with drop shadows."""
    
    DEFAULT_CSS = """
    TurboMenuBar {
        height: 3;
        width: 100%;
        background: $primary;
        color: white;
        content-align: left middle;
        padding: 0 2;
        border-bottom: heavy white;
    }
    
    TurboMenuBar Static {
        color: white;
        background: $primary;
    }
    """
    
    active_menu: reactive[Optional[str]] = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_items = ["File", "Edit", "Run", "Help"]
    
    def render(self) -> str:
        """Render the menu bar."""
        menu_text = "  ".join(f"[bold]{item}[/bold]" for item in self.menu_items)
        return f" {menu_text}"
    
    def on_click(self, event: events.Click) -> None:
        """Handle menu bar clicks."""
        # Determine which menu was clicked based on x coordinate
        x = event.x
        if 0 <= x < 8:
            self.app.action_show_file_menu()
        elif 8 <= x < 16:
            self.app.action_show_edit_menu()
        elif 16 <= x < 24:
            self.app.action_show_run_menu()
        elif 24 <= x < 32:
            self.app.action_show_help_menu()


class TurboStatusBar(Static):
    """Turbo Vision-style status bar showing task status."""
    
    DEFAULT_CSS = """
    TurboStatusBar {
        height: 1;
        width: 100%;
        background: $primary;
        color: white;
        content-align: center middle;
        dock: bottom;
    }
    """
    
    status_text: reactive[str] = reactive("Idle")
    
    def render(self) -> str:
        """Render the status bar."""
        return f" {self.status_text} "


class TurboWindow(Container):
    """Turbo Vision-style window with 3D appearance and shadow."""
    
    DEFAULT_CSS = """
    TurboWindow {
        width: 80%;
        height: 80%;
        border: heavy $primary;
        background: $surface;
        border-title-align: center;
        border-title-color: $primary;
        border-title-background: $surface;
        border-title-style: bold;
    }
    
    TurboWindow > Container {
        padding: 1 2;
    }
    """
    
    def __init__(self, title: str = "Window", **kwargs):
        super().__init__(**kwargs)
        self.border_title = f" {title} "


class MenuScreen(ModalScreen):
    """Base class for menu dropdown screens."""
    
    DEFAULT_CSS = """
    MenuScreen {
        align: left top;
    }
    
    MenuScreen > Container {
        width: 25;
        height: auto;
        background: $surface;
        border: heavy $primary;
        margin-top: 3;
    }
    
    MenuScreen Button {
        width: 100%;
        background: $surface;
        color: $text;
        border: none;
        text-align: left;
        padding: 0 2;
        height: 1;
    }
    
    MenuScreen Button:hover {
        background: $primary;
        color: white;
    }
    """
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
    ]
    
    def __init__(self, menu_items: List[tuple], x_offset: int = 0, **kwargs):
        """Initialize menu screen.
        
        Args:
            menu_items: List of (label, action) tuples
            x_offset: Horizontal offset for menu position
        """
        super().__init__(**kwargs)
        self.menu_items = menu_items
        self.x_offset = x_offset
    
    def compose(self) -> ComposeResult:
        """Compose the menu."""
        with Container():
            for label, action in self.menu_items:
                if label == "---":
                    yield Static("─" * 21)
                else:
                    yield Button(label, id=f"menu_{action}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu item selection."""
        button_id = event.button.id
        if button_id and button_id.startswith("menu_"):
            action = button_id[5:]  # Remove "menu_" prefix
            self.dismiss()
            # Call the action method on the app
            if hasattr(self.app, f"action_{action}"):
                method = getattr(self.app, f"action_{action}")
                method()


class FileMenuScreen(MenuScreen):
    """File menu dropdown."""
    
    def __init__(self, **kwargs):
        menu_items = [
            ("Status", "show_status"),
            ("Admins", "show_admins"),
            ("Rooms", "show_rooms"),
            ("---", ""),
            ("Exit", "quit"),
        ]
        super().__init__(menu_items, x_offset=1, **kwargs)


class EditMenuScreen(MenuScreen):
    """Edit menu dropdown."""
    
    def __init__(self, **kwargs):
        menu_items = [
            ("Sessions", "show_sessions"),
            ("Options", "show_options"),
        ]
        super().__init__(menu_items, x_offset=8, **kwargs)


class RunMenuScreen(MenuScreen):
    """Run menu dropdown."""
    
    def __init__(self, **kwargs):
        menu_items = [
            ("Send", "show_send"),
        ]
        super().__init__(menu_items, x_offset=16, **kwargs)


class HelpMenuScreen(MenuScreen):
    """Help menu dropdown."""
    
    def __init__(self, **kwargs):
        menu_items = [
            ("Show Log", "show_log"),
            ("About", "show_about"),
            ("Version", "show_version"),
        ]
        super().__init__(menu_items, x_offset=24, **kwargs)


# Import existing screens from the old TUI
# These will be reused with the new Turbo Vision style
from chatrixcd.tui import (
    BotStatusWidget,
    ActiveTasksWidget,
    AdminsScreen,
    RoomsScreen,
    SessionsScreen,
    SayScreen,
    LogScreen,
    SetScreen,
    ShowScreen,
    MessageScreen,
    OIDCAuthScreen,
)


class StatusScreen(Screen):
    """Screen to display bot status in Turbo Vision style."""
    
    DEFAULT_CSS = """
    StatusScreen {
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("enter", "app.pop_screen", "OK", priority=True),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Compose the status screen."""
        with TurboWindow(title="Bot Status"):
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
                yield Button("OK", id="ok_button", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "ok_button":
            self.app.pop_screen()


class OptionsScreen(Screen):
    """Combined Options screen merging SET and SHOW functionality."""
    
    DEFAULT_CSS = """
    OptionsScreen {
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]
    
    def __init__(self, tui_app, **kwargs):
        super().__init__(**kwargs)
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Compose the options screen."""
        with TurboWindow(title="Options"):
            with ScrollableContainer():
                yield Static("[bold]Configuration Options[/bold]\n")
                yield Button("Edit Settings", id="edit_settings", variant="primary")
                yield Button("View Configuration", id="view_config")
                yield Button("Manage Aliases", id="manage_aliases")
                yield Static("\n")
                yield Button("Close", id="close_button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "edit_settings":
            self.app.pop_screen()
            self.app.push_screen(SetScreen(self.tui_app))
        elif event.button.id == "view_config":
            self.app.pop_screen()
            # Show config
            import json
            import copy
            from chatrixcd.redactor import SensitiveInfoRedactor
            
            config_dict = copy.deepcopy(self.tui_app.config.config)
            sensitive_fields = ['password', 'access_token', 'api_token', 'client_secret', 'oidc_client_secret']
            
            def redact_sensitive(obj):
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
            self.app.push_screen(ShowScreen(config_text))
        elif event.button.id == "manage_aliases":
            self.app.pop_screen()
            from chatrixcd.tui import AliasesScreen
            self.app.push_screen(AliasesScreen(self.tui_app))
        elif event.button.id == "close_button":
            self.app.pop_screen()


class AboutScreen(Screen):
    """About screen showing application information."""
    
    DEFAULT_CSS = """
    AboutScreen {
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("enter", "app.pop_screen", "OK", priority=True),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the about screen."""
        with TurboWindow(title="About ChatrixCD"):
            with Container():
                yield Static("""
[bold cyan]ChatrixCD[/bold cyan]

Matrix bot for CI/CD automation through chat

[bold]Features:[/bold]
• End-to-end encrypted Matrix rooms
• Native Matrix authentication (password and OIDC/SSO)
• Interactive Text User Interface
• Semaphore UI integration
• Real-time task monitoring

[bold]License:[/bold] GPL v3
[bold]Repository:[/bold] github.com/CJFWeatherhead/ChatrixCD

[dim]This TUI uses a Turbo Vision-inspired design[/dim]
""")
                yield Button("OK", id="ok_button", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "ok_button":
            self.app.pop_screen()


class VersionScreen(Screen):
    """Version screen showing version information."""
    
    DEFAULT_CSS = """
    VersionScreen {
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("enter", "app.pop_screen", "OK", priority=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from chatrixcd import __version__
            self.version = __version__
        except ImportError:
            self.version = "Unknown"
    
    def compose(self) -> ComposeResult:
        """Compose the version screen."""
        with TurboWindow(title="Version Information"):
            with Container():
                yield Static(f"""
[bold cyan]ChatrixCD Version Information[/bold cyan]

[bold]Version:[/bold] {self.version}

[bold]Dependencies:[/bold]
• matrix-nio (Matrix client)
• aiohttp (HTTP client)
• textual (TUI framework)
• hjson (Configuration parser)
• colorlog (Logging)
• qrcode (QR code generation)

""")
                yield Button("OK", id="ok_button", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "ok_button":
            self.app.pop_screen()


class ChatrixTurboTUI(App):
    """ChatrixCD Turbo Vision-style Text User Interface."""
    
    # Define color themes
    THEMES = {
        'default': {
            'primary': '#4A9B7F',  # ChatrixCD brand green
            'surface': '#1E1E1E',
            'background': '#0D0D0D',
            'text': '#FFFFFF',
            'text-muted': '#808080',
        },
        'midnight': {
            'primary': '#0078D7',  # Midnight Commander blue
            'surface': '#000080',  # Dark blue
            'background': '#000040',
            'text': '#00FFFF',  # Cyan
            'text-muted': '#5F9EA0',
        },
        'grayscale': {
            'primary': '#808080',
            'surface': '#2F2F2F',
            'background': '#1A1A1A',
            'text': '#FFFFFF',
            'text-muted': '#A0A0A0',
        },
        'windows31': {
            'primary': '#008080',  # Teal
            'surface': '#C0C0C0',  # Silver
            'background': '#808080',  # Gray
            'text': '#000000',
            'text-muted': '#404040',
        },
        'msdos': {
            'primary': '#00AA00',  # Green
            'surface': '#000000',
            'background': '#000000',
            'text': '#FFAA00',  # Amber
            'text-muted': '#AA5500',
        }
    }
    
    CSS = """
    Screen {
        background: $background;
    }
    
    TurboMenuBar {
        background: $primary;
    }
    
    TurboStatusBar {
        background: $primary;
        color: $text;
    }
    
    TurboWindow {
        border: heavy $primary;
        background: $surface;
    }
    
    Button {
        margin: 1;
        min-width: 20;
    }
    
    Button.primary {
        background: $primary;
        color: $text;
    }
    
    Static#title {
        text-align: center;
        padding: 1;
        color: $text;
    }
    
    Container {
        height: 100%;
        padding: 1;
        background: $surface;
    }
    
    #main-content {
        height: 100%;
        align: center middle;
    }
    
    Label {
        color: $text;
    }
    
    Static {
        color: $text;
    }
    """
    
    TITLE = "ChatrixCD"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("f1", "show_file_menu", "File", priority=True),
        Binding("f2", "show_edit_menu", "Edit", priority=True),
        Binding("f3", "show_run_menu", "Run", priority=True),
        Binding("f4", "show_help_menu", "Help", priority=True),
    ]
    
    def __init__(self, bot, config, use_color: bool = True, theme: str = 'default', **kwargs):
        """Initialize the TUI.
        
        Args:
            bot: The ChatrixBot instance
            config: Configuration object
            use_color: Whether to use colors
            theme: Color theme to use ('default', 'midnight', 'grayscale', 'windows31', 'msdos')
        """
        # Set theme_name before calling super().__init__ because get_css_variables is called during init
        self.theme_name = theme if theme in self.THEMES else 'default'
        
        super().__init__(**kwargs)
        self.bot = bot
        self.config = config
        self.use_color = use_color
        self.start_time = time.time()
        self.messages_processed = 0
        self.errors = 0
        self.warnings = 0
        self.login_task = None
        self.bot_task = None
        self.pending_verifications_count = 0
        self.last_notified_verifications = set()
        
    def get_css_variables(self) -> Dict[str, str]:
        """Get CSS variables for the current theme.
        
        Returns:
            Dictionary of CSS variable names and values
        """
        theme = self.THEMES.get(self.theme_name, self.THEMES['default'])
        return {
            'primary': theme['primary'],
            'surface': theme['surface'],
            'background': theme['background'],
            'text': theme['text'],
            'text-muted': theme['text-muted'],
            'foreground': theme['text'],  # Alias for Textual 6.x compatibility
        }
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield TurboMenuBar()
        with Container(id="main-content"):
            with TurboWindow(title="ChatrixCD - Matrix CI/CD Bot"):
                with Container():
                    yield Static("[bold cyan]Welcome to ChatrixCD[/bold cyan]\n")
                    yield Static("[dim]Use the menu bar above to navigate[/dim]\n")
                    yield Static("F1 - File Menu   F2 - Edit Menu   F3 - Run Menu   F4 - Help Menu\n")
                    
                    # Add active tasks widget
                    tasks_widget = ActiveTasksWidget(id="active_tasks")
                    yield tasks_widget
        
        yield TurboStatusBar(id="status_bar")
    
    async def on_mount(self) -> None:
        """Called when the TUI is mounted."""
        # Start background task to update active tasks
        self.set_interval(5, self.update_active_tasks)
        
        # Start background task to update status bar
        self.set_interval(2, self.update_status_bar)
        
        # Start background task to check for pending verifications
        self.set_interval(3, self.check_pending_verifications)
        
        # If login task is set, perform login after TUI has started
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
    
    async def update_status_bar(self):
        """Update the status bar with current task status."""
        try:
            status_bar = self.query_one("#status_bar", TurboStatusBar)
            
            if self.bot and hasattr(self.bot, 'command_handler'):
                active_tasks = self.bot.command_handler.active_tasks
                
                if not active_tasks:
                    status_bar.status_text = "Idle"
                else:
                    running_count = 0
                    for task_id, task_info in active_tasks.items():
                        project_id = task_info.get('project_id')
                        try:
                            task_status = await self.bot.semaphore.get_task_status(project_id, task_id)
                            if task_status and task_status.get('status') == 'running':
                                running_count += 1
                        except Exception:
                            pass
                    
                    if running_count > 0:
                        status_bar.status_text = f"Running {running_count} task(s)"
                    else:
                        status_bar.status_text = f"{len(active_tasks)} task(s) (idle)"
            else:
                status_bar.status_text = "Bot not initialized"
        except Exception as e:
            logger.debug(f"Error updating status bar: {e}")
    
    async def check_pending_verifications(self):
        """Check for pending verification requests and notify user."""
        try:
            if not self.bot or not self.bot.client or not self.bot.client.olm:
                return
            
            client = self.bot.client
            current_verifications = set()
            
            if hasattr(client, 'key_verifications') and client.key_verifications:
                for transaction_id, verification in client.key_verifications.items():
                    current_verifications.add(transaction_id)
                    
                    if transaction_id not in self.last_notified_verifications:
                        if isinstance(verification, Sas):
                            other_device = getattr(verification, 'other_olm_device', None)
                            if other_device:
                                user_id = getattr(other_device, 'user_id', 'Unknown')
                                device_id = getattr(other_device, 'id', 'Unknown')
                            else:
                                user_id = 'Unknown'
                                device_id = 'Unknown'
                        else:
                            user_id = getattr(verification, 'user_id', 'Unknown')
                            device_id = getattr(verification, 'device_id', 'Unknown')
                        
                        logger.info(
                            f"New verification request from {user_id} (device: {device_id}). "
                            "Check Edit > Sessions menu to verify."
                        )
                        
                        self.notify(
                            f"New verification request from {user_id}",
                            severity="information",
                            timeout=10
                        )
            
            self.last_notified_verifications = current_verifications
            self.pending_verifications_count = len(current_verifications)
            
        except Exception as e:
            logger.debug(f"Error checking pending verifications: {e}")
    
    async def send_message_to_room(self, room_id: str, message: str):
        """Send a message to a room."""
        if self.bot:
            await self.bot.send_message(room_id, message)
            self.messages_processed += 1
    
    # Menu actions
    def action_show_file_menu(self):
        """Show File menu."""
        self.push_screen(FileMenuScreen())
    
    def action_show_edit_menu(self):
        """Show Edit menu."""
        self.push_screen(EditMenuScreen())
    
    def action_show_run_menu(self):
        """Show Run menu."""
        self.push_screen(RunMenuScreen())
    
    def action_show_help_menu(self):
        """Show Help menu."""
        self.push_screen(HelpMenuScreen())
    
    # File menu actions
    def action_show_status(self):
        """Show bot status screen."""
        self.push_screen(StatusScreen(self))
    
    def action_show_admins(self):
        """Show admin users screen."""
        bot_config = self.config.get_bot_config()
        admins = bot_config.get('admin_users', [])
        self.push_screen(AdminsScreen(admins))
    
    def action_show_rooms(self):
        """Show rooms screen."""
        rooms = []
        if self.bot and self.bot.client and self.bot.client.rooms:
            for room_id, room in self.bot.client.rooms.items():
                rooms.append({
                    'id': room_id,
                    'name': room.display_name or room_id
                })
        self.push_screen(RoomsScreen(rooms))
    
    def action_quit(self):
        """Handle quit action."""
        self.exit()
    
    # Edit menu actions
    def action_show_sessions(self):
        """Show session management screen."""
        self.push_screen(SessionsScreen(self))
    
    def action_show_options(self):
        """Show options screen (merged SET and SHOW)."""
        self.push_screen(OptionsScreen(self))
    
    # Run menu actions
    def action_show_send(self):
        """Show message sending screen (formerly Say)."""
        rooms = []
        if self.bot and self.bot.client and self.bot.client.rooms:
            for room_id, room in self.bot.client.rooms.items():
                rooms.append({
                    'id': room_id,
                    'name': room.display_name or room_id
                })
        self.push_screen(SayScreen(self, rooms))
    
    # Help menu actions
    def action_show_log(self):
        """Show log screen."""
        log_content = ""
        log_file = self.config.get('bot.log_file', 'chatrixcd.log')
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                reversed_lines = lines[-1000:]
                reversed_lines.reverse()
                log_content = ''.join(reversed_lines)
        except FileNotFoundError:
            log_content = f"Log file not found: {log_file}"
        except Exception as e:
            log_content = f"Error reading log: {e}"
        
        self.push_screen(LogScreen(log_content))
    
    def action_show_about(self):
        """Show about screen."""
        self.push_screen(AboutScreen())
    
    def action_show_version(self):
        """Show version screen."""
        self.push_screen(VersionScreen())


async def run_tui(bot, config, use_color: bool = True, mouse: bool = False):
    """Run the Turbo Vision-style TUI interface.
    
    Args:
        bot: The ChatrixBot instance
        config: Configuration object
        use_color: Whether to use colors
        mouse: Whether to enable mouse support (default: False)
    """
    app = ChatrixTurboTUI(bot, config, use_color=use_color)
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
        
        TurboWindow {
            border: heavy #4A9B7F;
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
        
        BINDINGS = [
            Binding("q", "quit", "Quit", priority=True),
            Binding("escape", "quit", "Quit", priority=True),
        ]
        
        def __init__(self, config_text: str, **kwargs):
            super().__init__(**kwargs)
            self.config_text = config_text
        
        def compose(self) -> ComposeResult:
            """Create child widgets."""
            with TurboWindow(title="Configuration"):
                with Container():
                    yield Static("[bold cyan]Configuration[/bold cyan]\n", id="title")
                    yield TextArea(self.config_text, read_only=True, id="config_area")
        
        async def action_quit(self):
            """Handle quit action."""
            self.exit()
    
    app = ConfigViewerApp(config_text)
    await app.run_async()
