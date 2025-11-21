"""TUI integration for OIDC authentication plugin."""

import asyncio
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Input, Label
from textual.screen import ModalScreen
from textual.binding import Binding

from chatrixcd.tui.plugin_integration import PluginTUIExtension
from chatrixcd.tui.registry import ScreenRegistration


class OIDCAuthScreen(ModalScreen):
    """Modal screen for OIDC token input."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]
    
    CSS = """
    OIDCAuthScreen {
        align: center middle;
    }
    
    OIDCAuthScreen > Container {
        width: 80;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2;
    }
    
    .auth-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .auth-instructions {
        margin: 1 0;
        color: $text;
    }
    
    .auth-url {
        background: $panel;
        padding: 1;
        margin: 1 0;
        color: $warning;
        text-style: bold;
    }
    
    .provider-list {
        margin: 1 0;
        padding: 1;
        background: $panel;
    }
    
    .input-container {
        margin: 1 0;
    }
    
    .button-container {
        margin-top: 1;
        height: auto;
        align: center middle;
    }
    
    .button-container Button {
        margin: 0 1;
    }
    """

    @classmethod
    def formatted_css(cls, theme: dict) -> str:
        """Return CSS with theme variables substituted.

        This helps avoid Textual's UnresolvedVariableError when running
        unit tests outside a full TUI environment.
        """
        css = cls.CSS
        # Replace simple $var occurrences with provided theme values
        for k, v in theme.items():
            css = css.replace(f"${k}", v)
        return css
    
    def __init__(self, sso_url: str, redirect_url: str, identity_providers: list):
        """Initialize OIDC auth screen.
        
        Args:
            sso_url: SSO authentication URL
            redirect_url: Redirect URL for callback
            identity_providers: List of available identity providers
        """
        super().__init__()
        self.sso_url = sso_url
        self.redirect_url = redirect_url
        self.identity_providers = identity_providers
        self.token_future = asyncio.Future()
        
    def compose(self):
        """Compose the OIDC auth screen."""
        with Container():
            yield Static("🔐 OIDC Authentication Required", classes="auth-title")
            
            yield Static(
                "Please complete these steps to authenticate:",
                classes="auth-instructions"
            )
            
            yield Static("1. Open this URL in your browser:", classes="auth-instructions")
            yield Static(self.sso_url, classes="auth-url")
            
            yield Static("2. Log in with your credentials", classes="auth-instructions")
            
            yield Static(
                f"3. After login, you'll be redirected to:\n   {self.redirect_url}?loginToken=...",
                classes="auth-instructions"
            )
            
            # Show available identity providers if multiple
            if self.identity_providers and len(self.identity_providers) > 1:
                providers_text = "Available Identity Providers:\n"
                for i, idp in enumerate(self.identity_providers, 1):
                    providers_text += f"  {i}. {idp.get('name', idp.get('id', 'Unknown'))}\n"
                yield Static(providers_text, classes="provider-list")
            
            yield Static(
                "4. Copy the 'loginToken' value from the URL and paste it below:",
                classes="auth-instructions"
            )
            
            with Vertical(classes="input-container"):
                yield Label("Login Token:")
                yield Input(
                    placeholder="Paste your login token here",
                    id="token-input"
                )
            
            with Horizontal(classes="button-container"):
                yield Button("Submit", variant="primary", id="submit-btn")
                yield Button("Cancel", variant="error", id="cancel-btn")
    
    def on_mount(self):
        """Focus the input when screen mounts."""
        self.query_one("#token-input").focus()
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "submit-btn":
            await self.submit_token()
        elif event.button.id == "cancel-btn":
            await self.cancel()
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle enter key in input field."""
        await self.submit_token()
    
    async def submit_token(self):
        """Submit the login token."""
        token_input = self.query_one("#token-input")
        token = token_input.value.strip()
        
        if not token:
            # Show error
            token_input.value = ""
            token_input.placeholder = "Error: Token cannot be empty"
            return
        
        # Set result and dismiss
        if not self.token_future.done():
            self.token_future.set_result(token)
        self.dismiss(token)
    
    async def cancel(self):
        """Cancel authentication."""
        if not self.token_future.done():
            self.token_future.set_result(None)
        self.dismiss(None)
    
    def action_cancel(self):
        """Handle escape/ctrl+c to cancel."""
        self.app.call_later(self.cancel)


class OIDCAuthPluginTUI(PluginTUIExtension):
    """TUI extension for OIDC authentication plugin."""
    
    def __init__(self, plugin):
        """Initialize TUI extension.
        
        Args:
            plugin: OIDCAuthPlugin instance
        """
        super().__init__(plugin)
        
        # Register token callback with plugin
        plugin.set_token_callback(self.token_callback)
    
    async def token_callback(self, sso_url: str, redirect_url: str, identity_providers: list) -> str:
        """Callback to get token from TUI.
        
        Args:
            sso_url: SSO authentication URL
            redirect_url: Redirect URL for callback
            identity_providers: List of available identity providers
            
        Returns:
            Login token from user
        """
        # This will be called by the plugin when OIDC auth is needed
        # We need to push the screen and wait for result
        screen = OIDCAuthScreen(sso_url, redirect_url, identity_providers)
        
        # Get the app instance (assumes this is called in TUI context)
        # The bot's TUI app should be accessible
        tui_app = getattr(self.plugin.bot_instance, 'tui_app', None)
        
        if not tui_app:
            # TUI not available, fall back to console
            self.plugin.logger.warning("TUI not available for OIDC callback, using console input")
            return None
        
        # Push screen and wait for result
        token = await tui_app.push_screen_wait(screen)
        return token
    
    def get_screen_registrations(self) -> list:
        """Get screen registrations for this plugin.
        
        Note: OIDC auth screen is modal and shown on-demand, not in main menu.
        
        Returns:
            Empty list (no menu screens to register)
        """
        # OIDC screen is a modal dialog, not a main menu item
        return []
