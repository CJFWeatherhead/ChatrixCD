# TUI Migration Guide: Classic to Turbo Vision

This document explains the migration from the original ChatrixCD TUI to the new Turbo Vision-style interface.

## Overview

The new Turbo Vision-style TUI (`chatrixcd/tui_turbo.py`) provides a more classic, windowed interface inspired by the Turbo Vision framework, while maintaining all the functionality of the original TUI (`chatrixcd/tui.py`).

## What Changed

### 1. Menu Organization

**Old TUI**: Button-based main menu with direct access to functions
```
Main Screen:
- STATUS button
- ADMINS button
- ROOMS button
- SESSIONS button
- SAY button
- LOG button
- SET button
- SHOW button
- ALIASES button
- QUIT button
```

**New TUI**: Menu bar with logical groupings
```
Menu Bar: File | Edit | Run | Help

File Menu:
- Status
- Admins
- Rooms
- Exit

Edit Menu:
- Sessions
- Options (merged SET + SHOW)

Run Menu:
- Send (renamed from Say)

Help Menu:
- Show Log
- About
- Version
```

### 2. Visual Style

**Old TUI**:
- Header widget at top
- Footer widget at bottom
- Button-based navigation
- Simple styling

**New TUI**:
- Menu bar with F-key shortcuts (F1-F4)
- 3D windowed appearance with shadows
- Status bar showing task status
- ChatrixCD brand colors (#4A9B7F green)
- Drop-down menus
- Modal dialogs with borders

### 3. Key Bindings

**Old TUI**:
- `s` - Status
- `a` - Admins
- `r` - Rooms
- `e` - Sessions
- `m` - Say
- `l` - Log
- `t` - Set
- `c` - Show Config
- `x` - Aliases
- `q` - Quit

**New TUI**:
- `F1` - File menu
- `F2` - Edit menu
- `F3` - Run menu
- `F4` - Help menu
- `Escape` - Close current screen/menu
- `Ctrl+C` - Quit

### 4. Merged Functionality

The new TUI combines SET and SHOW into a single **Options** screen under the Edit menu:

**Options Screen**:
- Edit Settings (formerly SET)
- View Configuration (formerly SHOW)
- Manage Aliases

This provides a more cohesive configuration management experience.

### 5. Renamed Components

- **Say** → **Send**: The message sending functionality is now called "Send" and is accessible via Run > Send
- **SET/SHOW** → **Options**: Configuration viewing and editing are now unified under Edit > Options

### 6. Status Bar

The new TUI includes a dynamic status bar at the bottom that shows:
- "Idle" - When no tasks are running
- "Running X task(s)" - When tasks are active

This provides at-a-glance information about bot activity.

## Implementation Details

### File Structure

```
chatrixcd/
├── tui.py          # Original TUI (still available)
├── tui_turbo.py    # New Turbo Vision TUI (active by default)
└── main.py         # Updated to use tui_turbo by default
```

### Module Imports

The new Turbo Vision TUI reuses many components from the original TUI:
- `BotStatusWidget`
- `ActiveTasksWidget`
- `AdminsScreen`
- `RoomsScreen`
- `SessionsScreen`
- `SayScreen`
- `LogScreen`
- `SetScreen`
- `ShowScreen`
- `MessageScreen`
- `OIDCAuthScreen`

New components specific to Turbo Vision style:
- `TurboMenuBar` - Menu bar widget
- `TurboStatusBar` - Status bar widget
- `TurboWindow` - Window container with 3D borders and shadows
- `FileMenuScreen`, `EditMenuScreen`, `RunMenuScreen`, `HelpMenuScreen` - Menu dropdowns
- `StatusScreen` - Turbo-styled status display
- `OptionsScreen` - Unified configuration management
- `AboutScreen` - Application information
- `VersionScreen` - Version and dependencies

### Color Scheme

The Turbo Vision TUI uses ChatrixCD brand colors:

```python
# Menu bar background
background: #4A9B7F (ChatrixCD Green)

# Status bar background
background: #2D3238 (Dark Gray)

# Window borders
border: #4A9B7F (ChatrixCD Green)

# Primary buttons
background: #4A9B7F (ChatrixCD Green)
color: white
```

### CSS Styling

The new TUI includes custom CSS for the Turbo Vision aesthetic:

```css
TurboMenuBar {
    height: 3;
    width: 100%;
    background: $primary;
    color: white;
    border-bottom: heavy white;
}

TurboStatusBar {
    height: 1;
    width: 100%;
    background: $primary;
    color: white;
    dock: bottom;
}

TurboWindow {
    width: 80%;
    height: 80%;
    border: heavy $primary;
    background: $surface;
}
```

## Testing

### Unit Tests

All existing TUI tests continue to pass. New tests have been added for Turbo Vision components:

```python
# tests/test_tui.py

class TestTurboTUIComponents(unittest.TestCase):
    """Test Turbo Vision TUI components."""
    
    def test_turbo_menu_bar_creation(self):
        """Test creating a TurboMenuBar widget."""
        ...
    
    def test_turbo_status_bar_creation(self):
        """Test creating a TurboStatusBar widget."""
        ...
    
    def test_turbo_window_creation(self):
        """Test creating a TurboWindow container."""
        ...
```

### Manual Testing

To test the new TUI:

```bash
# Run the bot in TUI mode (default)
python -m chatrixcd.main

# Run in log-only mode (bypasses TUI)
python -m chatrixcd.main -L
```

## Backward Compatibility

The original TUI (`chatrixcd/tui.py`) remains available and can be restored by changing the imports in `chatrixcd/main.py`:

```python
# To use the original TUI:
from chatrixcd.tui import run_tui, show_config_tui

# To use the Turbo Vision TUI (current default):
from chatrixcd.tui_turbo import run_tui, show_config_tui
```

## Migration Checklist

If you're updating from the old TUI to the new Turbo Vision TUI:

- [x] Menu items reorganized into File, Edit, Run, Help
- [x] SET and SHOW merged into Options
- [x] Say renamed to Send
- [x] Added About and Version to Help menu
- [x] Status bar shows task status
- [x] 3D windowed appearance with shadows
- [x] ChatrixCD brand colors applied
- [x] F-key shortcuts for menu access
- [x] All existing functionality preserved
- [x] Tests updated to cover new components

## Documentation

See also:
- [TUI_TURBO_VISION_DESIGN.md](TUI_TURBO_VISION_DESIGN.md) - Complete design documentation with screenshots
- [QUICKSTART.md](../QUICKSTART.md) - Getting started guide
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture

## Questions or Issues

If you encounter any issues with the new TUI or have questions about the migration:

1. Check the [documentation](https://chatrixcd.cjfw.me/)
2. Review the [TUI design document](TUI_TURBO_VISION_DESIGN.md)
3. Open an issue on [GitHub](https://github.com/CJFWeatherhead/ChatrixCD/issues)

---

*Last updated: 2025-10-21*
