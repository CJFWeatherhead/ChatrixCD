"""Public TUI API and lightweight compatibility shims.

This module exposes the main TUI classes used by the application and a
few minimal compatibility shims that the unit tests (and some plugins)
expect to import. Keep the shims small and well-typed so they are easy
to maintain and refactor later.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional

from .app import ChatrixTUI, run_tui
from .events import (
    TUIEvent,
    ScreenChangeEvent,
    DataUpdateEvent,
)
from .screens.base import BaseScreen
from .widgets.base import BaseWidget
from .widgets.common import MetricDisplay

# Import core screens where available
from .screens.main_menu import (
    MainMenuScreen,
)
from .screens.rooms import (
    RoomsScreen,
)
from .screens.status import (
    StatusScreen,
)
from .screens.logs import (
    LogsScreen,
)
from .screens.config import (
    ConfigScreen,
)

# --- Compatibility shims ---


class AdminsScreen(BaseScreen):
    """Minimal admins screen used by older tests/plugins.

    Holds a simple list of admin identifiers and renders a static block
    when composed by Textual. The constructor intentionally accepts
    arbitrary args/kwargs to remain compatible with previous call sites.
    """

    SCREEN_TITLE = "Admins"

    def __init__(self, admins: Optional[Iterable[Any]] = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.admins: List[str] = list(map(str, admins or []))

    def compose_content(self):
        from textual.widgets import Static

        header = "[bold]Admins[/bold]"
        content_lines = [header] + self.admins
        yield Static("\n".join(content_lines))


class SessionsScreen(BaseScreen):
    """Minimal sessions screen used by older tests/plugins."""

    SCREEN_TITLE = "Sessions"

    def __init__(
        self,
        sessions: Optional[Iterable[Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.sessions: List[str] = list(map(str, sessions or []))

    def compose_content(self):
        from textual.widgets import Static

        header = "[bold]Sessions[/bold]"
        content_lines = [header] + self.sessions
        yield Static("\n".join(content_lines))


class MessageScreen:
    """Minimal message container expected by some callers/tests."""

    def __init__(self, message: str) -> None:
        self.message = message


class BotStatusWidget:
    """Lightweight status holder used in tests.

    This is a minimal, plain-Python holder used by unit tests that do
    not instantiate the real UI widget.
    """

    def __init__(self) -> None:
        self.matrix_status: str = "Disconnected"
        self.semaphore_status: str = "Unknown"
        self.messages_sent: int = 0
        self.requests_received: int = 0
        self.errors: int = 0
        self.emojis_used: int = 0


class ActiveTasksWidget(MetricDisplay):
    """Widget used by tests to inspect and update active tasks state."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            *args,
            label="Active Tasks",
            value=0,
            icon="🔧",
            **kwargs,
        )
        self.tasks: List[Any] = []

    def update_tasks(self, tasks: Iterable[Any] | dict[str, Any]) -> None:
        """Update internal list and displayed count.

        Accept either an iterable of tasks or a dict mapping IDs to task
        objects (the tests sometimes provide both shapes).
        """

        if tasks is None:
            self.tasks = []
            self.value = 0
            return

        if isinstance(tasks, dict):
            self.tasks = list(tasks.values())
        else:
            self.tasks = list(tasks)

        try:
            self.value = len(self.tasks)
        except Exception:
            self.value = 0


# Minimal OIDC screen placeholder
class OIDCAuthScreen:
    def __init__(
        self,
        sso_url: str,
        redirect_url: str,
        identity_providers: list[Any],
    ) -> None:
        self.sso_url = sso_url
        self.redirect_url = redirect_url
        self.identity_providers = identity_providers
        self.token: Optional[str] = None

    def compose(self) -> list:
        return []


# Aliases screen provided by plugin integration (optional)
try:
    from .plugins.aliases_tui import AliasesScreen  # type: ignore
except Exception:  # pragma: no cover - optional plugin
    AliasesScreen = None


async def show_config_tui(
    *args: Any, **kwargs: Any
) -> None:  # pragma: no cover - compatibility stub
    """Compatibility stub for tests that expect a coroutine to exist."""


__all__ = [
    "ChatrixTUI",
    "run_tui",
    "TUIEvent",
    "ScreenChangeEvent",
    "DataUpdateEvent",
    "BaseScreen",
    "BaseWidget",
    "MainMenuScreen",
    "RoomsScreen",
    "StatusScreen",
    "LogsScreen",
    "ConfigScreen",
    "AliasesScreen",
    "AdminsScreen",
    "SessionsScreen",
    "MessageScreen",
    "BotStatusWidget",
    "ActiveTasksWidget",
    "OIDCAuthScreen",
    "show_config_tui",
]
