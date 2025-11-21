"""Event system for TUI.

Provides type-safe events for communication between TUI components.
"""

from typing import Any, Optional
from textual.message import Message


class TUIEvent(Message):
    """Base class for all TUI events."""
    
    def __init__(self, source: str, data: Optional[dict] = None):
        super().__init__()
        self.source = source
        self.data = data or {}


class ScreenChangeEvent(TUIEvent):
    """Event fired when screen changes."""
    
    def __init__(self, screen_name: str, previous_screen: Optional[str] = None):
        super().__init__(source="screen_manager")
        self.screen_name = screen_name
        self.previous_screen = previous_screen


class DataUpdateEvent(TUIEvent):
    """Event fired when data updates occur."""
    
    def __init__(self, data_type: str, data: Any):
        super().__init__(source="data_manager")
        self.data_type = data_type
        self.data_payload = data


class PluginLoadedEvent(TUIEvent):
    """Event fired when a plugin is loaded."""
    
    def __init__(self, plugin_name: str, plugin_type: str):
        super().__init__(source="plugin_manager")
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type


class PluginUnloadedEvent(TUIEvent):
    """Event fired when a plugin is unloaded."""
    
    def __init__(self, plugin_name: str):
        super().__init__(source="plugin_manager")
        self.plugin_name = plugin_name


class TaskUpdateEvent(TUIEvent):
    """Event fired when task status updates."""
    
    def __init__(self, task_id: int, status: str, project_id: int):
        super().__init__(source="task_monitor")
        self.task_id = task_id
        self.status = status
        self.project_id = project_id


class RoomJoinedEvent(TUIEvent):
    """Event fired when bot joins a room."""
    
    def __init__(self, room_id: str, room_name: str):
        super().__init__(source="matrix_client")
        self.room_id = room_id
        self.room_name = room_name


class RoomLeftEvent(TUIEvent):
    """Event fired when bot leaves a room."""
    
    def __init__(self, room_id: str):
        super().__init__(source="matrix_client")
        self.room_id = room_id


class ConfigChangedEvent(TUIEvent):
    """Event fired when configuration changes."""
    
    def __init__(self, config_key: str, old_value: Any, new_value: Any):
        super().__init__(source="config_manager")
        self.config_key = config_key
        self.old_value = old_value
        self.new_value = new_value


class NotificationEvent(TUIEvent):
    """Event for displaying notifications to user."""
    
    def __init__(self, message: str, severity: str = "information"):
        super().__init__(source="notification_manager")
        self.message = message
        self.severity = severity  # "information", "warning", "error", "success"
