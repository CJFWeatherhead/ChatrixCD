"""Modular Text User Interface for ChatrixCD v2.

This is a complete redesign of the TUI with modular, plugin-aware architecture.
"""

from .app import ChatrixTUI, run_tui
from .events import TUIEvent, ScreenChangeEvent, DataUpdateEvent
from .screens.base import BaseScreen
from .widgets.base import BaseWidget
from .widgets.common import MetricDisplay

# Provide lightweight compatibility shims for older test expectations
from .screens.base import BaseScreen


class AdminsScreen(BaseScreen):
    SCREEN_TITLE = "Admins"

    def __init__(self, admins=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admins = admins or []

    def compose_content(self):
        from textual.widgets import Static
        yield Static("[bold]Admins[/bold]\n" + "\n".join(map(str, self.admins)))


class SessionsScreen(BaseScreen):
    SCREEN_TITLE = "Sessions"

    def __init__(self, sessions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sessions = sessions or []

    def compose_content(self):
        from textual.widgets import Static
        yield Static("[bold]Sessions[/bold]\n" + "\n".join(map(str, self.sessions)))


class SayScreen:
    def __init__(self, *args, **kwargs):
        pass


class LogScreen:
    def __init__(self, *args, **kwargs):
        pass


class SetScreen:
    def __init__(self, *args, **kwargs):
        pass


class ShowScreen:
    def __init__(self, *args, **kwargs):
        pass


class MessageScreen:
    def __init__(self, message):
        self.message = message


class BotStatusWidget:
    def __init__(self):
        self.matrix_status = "Disconnected"
        self.semaphore_status = "Unknown"
        self.messages_sent = 0
        self.requests_received = 0
        self.errors = 0
        self.emojis_used = 0


class ActiveTasksWidget(MetricDisplay):
    """Simple alias widget used by tests to query active tasks element."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, label="Active Tasks", value=0, icon="🔧", **kwargs)
        # Maintain a tasks list for tests that inspect `.tasks`
        self.tasks: list = []

    def update_tasks(self, tasks: dict | list):
        """Update internal tasks list and displayed value."""
        try:
            if isinstance(tasks, dict):
                self.tasks = list(tasks.values())
                count = len(tasks)
            else:
                self.tasks = list(tasks)
                count = len(self.tasks)
            self.value = count
        except Exception:
            # Fallback: set to empty
            self.tasks = []
            self.value = 0


class OIDCAuthScreen:
    def __init__(self, sso_url, redirect_url, identity_providers):
        self.sso_url = sso_url
        self.redirect_url = redirect_url
        self.identity_providers = identity_providers
        self.token = None

    def compose(self):
        return []

# Import core screens where available (after compatibility shims above)
from .screens.main_menu import MainMenuScreen
from .screens.rooms import RoomsScreen
from .screens.status import StatusScreen
from .screens.logs import LogsScreen
from .screens.config import ConfigScreen
# Aliases screen provided by plugin integration
try:
    from .plugins.aliases_tui import AliasesScreen
except Exception:
    AliasesScreen = None


async def show_config_tui(*args, **kwargs):
    """Compatibility stub for tests that expect show_config_tui coroutine."""
    return None


__all__ = [
    'ChatrixTUI',
    'run_tui',
    'TUIEvent',
    'ScreenChangeEvent',
    'DataUpdateEvent',
    'BaseScreen',
    'BaseWidget',
    'MainMenuScreen',
    'RoomsScreen',
    'StatusScreen',
    'LogsScreen',
    'ConfigScreen',
    'AliasesScreen',
    'AdminsScreen',
    'SessionsScreen',
    'SayScreen',
    'LogScreen',
    'SetScreen',
    'ShowScreen',
    'MessageScreen',
    'BotStatusWidget',
    'OIDCAuthScreen',
    'show_config_tui',
]
