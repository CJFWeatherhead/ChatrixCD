"""Configuration screen for viewing and editing config."""

import json
import copy
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Button, TextArea
from textual.binding import Binding
from .base import BaseScreen
from chatrixcd.redactor import SensitiveInfoRedactor


class ConfigScreen(BaseScreen):
    """Screen for viewing and editing configuration."""
    
    SCREEN_TITLE = "Configuration"
    
    BINDINGS = [
        Binding("escape", "go_back", "Back", priority=True),
        Binding("b", "go_back", "Back"),
        Binding("e", "edit_mode", "Edit"),
        Binding("s", "save_config", "Save"),
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize config screen."""
        super().__init__(*args, **kwargs)
        self.edit_mode = False
        self.pending_changes = {}
        
    def compose_content(self):
        """Compose config screen content."""
        with Container(classes="config-container"):
            yield Static("[bold cyan]Configuration[/bold cyan]", classes="section-header")
            yield Static(
                "Current bot configuration (sensitive values redacted):",
                classes="description"
            )
            
            yield TextArea(
                id="config-content",
                language="json",
                read_only=True,
                classes="config-viewer"
            )
            
            with Vertical(classes="config-actions"):
                yield Button("Edit Mode", id="edit-button", variant="primary")
                yield Button("Save Changes", id="save-button", variant="success", disabled=True)
                yield Button("Discard Changes", id="discard-button", variant="default", disabled=True)
                
            yield Static(id="status-message", classes="status-message")
            
    async def on_screen_mount(self):
        """Load config when screen mounts."""
        await self.refresh_data()
        
    async def refresh_data(self):
        """Refresh configuration display."""
        try:
            # Deep copy config to avoid modifying original
            config_dict = copy.deepcopy(self.tui_app.config.config)
            
            # Redact sensitive fields
            redactor = SensitiveInfoRedactor()
            config_dict = redactor.redact_dict(config_dict)
            
            # Format as JSON
            config_text = json.dumps(config_dict, indent=2)
            
            # Update text area
            text_area = self.query_one("#config-content", TextArea)
            text_area.text = config_text
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            await self.show_error(f"Failed to load configuration: {e}")
            
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "edit-button":
            await self.toggle_edit_mode()
        elif event.button.id == "save-button":
            await self.save_changes()
        elif event.button.id == "discard-button":
            await self.discard_changes()
            
    async def toggle_edit_mode(self):
        """Toggle between view and edit mode."""
        text_area = self.query_one("#config-content", TextArea)
        edit_button = self.query_one("#edit-button", Button)
        save_button = self.query_one("#save-button", Button)
        discard_button = self.query_one("#discard-button", Button)
        
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            text_area.read_only = False
            edit_button.label = "View Mode"
            save_button.disabled = False
            discard_button.disabled = False
            await self.show_notification("Edit mode enabled", "information")
        else:
            text_area.read_only = True
            edit_button.label = "Edit Mode"
            save_button.disabled = True
            discard_button.disabled = True
            await self.show_notification("View mode enabled", "information")
            
    async def save_changes(self):
        """Save configuration changes."""
        try:
            text_area = self.query_one("#config-content", TextArea)
            config_text = text_area.text
            
            # Parse JSON
            try:
                new_config = json.loads(config_text)
            except json.JSONDecodeError as e:
                await self.show_error(f"Invalid JSON: {e}")
                return
                
            # Validate and save
            # Note: This is a simplified version. In production, you'd want
            # more sophisticated validation and merging logic
            
            config_file = getattr(self.tui_app.config, 'config_file', 'config.json')
            
            with open(config_file, 'w') as f:
                json.dump(new_config, f, indent=2)
                
            await self.show_success("Configuration saved successfully")
            
            # Reload config
            self.tui_app.config.load_config()
            await self.refresh_data()
            
            # Exit edit mode
            await self.toggle_edit_mode()
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            await self.show_error(f"Failed to save configuration: {e}")
            
    async def discard_changes(self):
        """Discard configuration changes."""
        await self.refresh_data()
        await self.toggle_edit_mode()
        await self.show_notification("Changes discarded", "information")
        
    def action_edit_mode(self):
        """Toggle edit mode action."""
        self.app.call_later(self.toggle_edit_mode)
        
    def action_save_config(self):
        """Save config action."""
        if self.edit_mode:
            self.app.call_later(self.save_changes)
