# ChatrixCD Turbo Vision-Style TUI Design

This document showcases the new Turbo Vision-inspired Text User Interface design for ChatrixCD.

## Design Overview

The new TUI features:

- **Menu bar** at the top with File, Edit, Run, Help menus
- **Classic 3D aesthetic** with box-drawing characters and drop shadows
- **Status bar** at the bottom showing idle/running task status
- **ChatrixCD brand colors** (#4A9B7F green for highlights and borders)
- **Windowed appearance** with modal dialogs and shadows
- **Logical menu organization** based on functionality

## Color Scheme

- **Menu bar background**: #4A9B7F (ChatrixCD Green)
- **Status bar background**: #2D3238 (Dark Gray)
- **Window borders**: #4A9B7F (ChatrixCD Green)
- **Shadows**: Dark gray (░ character)
- **Primary buttons**: #4A9B7F background with white text
- **Regular text**: White on dark background

## Screenshots

### 1. Main Screen

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║    ╔══════════════════════════════════════════════════════════════════╗      ║
║    ║                   ChatrixCD - Matrix CI/CD Bot                   ║      ║
║    ╠══════════════════════════════════════════════════════════════════╣      ║
║    ║                                                                  ║░     ║
║    ║  Welcome to ChatrixCD                                            ║░     ║
║    ║                                                                  ║░     ║
║    ║  Use the menu bar above to navigate:                            ║░     ║
║    ║                                                                  ║░     ║
║    ║  F1 - File Menu   F2 - Edit Menu   F3 - Run Menu   F4 - Help   ║░     ║
║    ║                                                                  ║░     ║
║    ║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║░     ║
║    ║                                                                  ║░     ║
║    ║  Active Tasks                                                    ║░     ║
║    ║                                                                  ║░     ║
║    ║  No active tasks                                                 ║░     ║
║    ║                                                                  ║░     ║
║    ║                                                                  ║░     ║
║    ║                                                                  ║░     ║
║    ║                                                                  ║░     ║
║    ║                                                                  ║░     ║
║    ╚══════════════════════════════════════════════════════════════════╝░     ║
║      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░       ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Idle                                                                           ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

The main screen features:
- Menu bar at top with File, Edit, Run, Help (highlighted in ChatrixCD green)
- Central window with 3D appearance and drop shadow
- Status bar at bottom showing current task status
- Active tasks display area

### 2. File Menu

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ ╔═══════════════╗                                                              ║
║ ║ Status        ║                                                              ║
║ ║ Admins        ║                                                              ║
║ ║ Rooms         ║                                                              ║
║ ║ ───────────── ║                                                              ║
║ ║ Exit          ║                                                              ║
║ ╚═══════════════╝░                                                             ║
║   ░░░░░░░░░░░░░░░                                                              ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

File menu options:
- **Status**: View bot status (Matrix connection, Semaphore status, uptime, metrics)
- **Admins**: View list of admin users
- **Rooms**: View list of joined Matrix rooms
- **Exit**: Quit the application

### 3. Edit Menu

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║        ╔═══════════════╗                                                        ║
║        ║ Sessions      ║                                                        ║
║        ║ Options       ║                                                        ║
║        ╚═══════════════╝░                                                       ║
║          ░░░░░░░░░░░░░░░                                                        ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

Edit menu options:
- **Sessions**: Manage encryption sessions, verify devices, view pending verifications
- **Options**: Merged SET and SHOW functionality - edit settings, view configuration, manage aliases

### 4. Run Menu

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║               ╔═══════════════╗                                                 ║
║               ║ Send          ║                                                 ║
║               ╚═══════════════╝░                                                ║
║                 ░░░░░░░░░░░░░░░                                                 ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

Run menu options:
- **Send**: Send messages to Matrix rooms (formerly "Say")

### 5. Help Menu

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                    ╔═══════════════╗                                            ║
║                    ║ Show Log      ║                                            ║
║                    ║ About         ║                                            ║
║                    ║ Version       ║                                            ║
║                    ╚═══════════════╝░                                           ║
║                      ░░░░░░░░░░░░░░░                                            ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

Help menu options:
- **Show Log**: View application logs
- **About**: Show application information and features
- **Version**: Display version information and dependencies

### 6. Status Window

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║         ╔═══════════════════════════════════════════════════════╗             ║
║         ║                     Bot Status                        ║             ║
║         ╠═══════════════════════════════════════════════════════╣             ║
║         ║                                                       ║░            ║
║         ║  Bot Status                                           ║░            ║
║         ║                                                       ║░            ║
║         ║  Matrix: Connected                                    ║░            ║
║         ║  Semaphore: Connected                                 ║░            ║
║         ║  Uptime: 2h 15m 30s                                   ║░            ║
║         ║                                                       ║░            ║
║         ║  Metrics                                              ║░            ║
║         ║  Messages Processed: 42                               ║░            ║
║         ║  Errors: 0                                            ║░            ║
║         ║  Warnings: 1                                          ║░            ║
║         ║                                                       ║░            ║
║         ║               [ OK ]                                  ║░            ║
║         ║                                                       ║░            ║
║         ╚═══════════════════════════════════════════════════════╝░            ║
║           ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Running 2 task(s)                                                              ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

Modal window example showing:
- 3D window with border and shadow
- Bot connection status
- Runtime metrics
- Primary action button in ChatrixCD green
- Status bar updating to show running tasks

### 7. Options Window (Edit > Options)

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║         ╔═══════════════════════════════════════════════════════╗             ║
║         ║                      Options                        ║             ║
║         ╠═══════════════════════════════════════════════════════╣             ║
║         ║                                                       ║░            ║
║         ║  Configuration Options                               ║░            ║
║         ║                                                       ║░            ║
║         ║           [ Edit Settings ]                         ║░            ║
║         ║                                                       ║░            ║
║         ║           [ View Configuration ]                     ║░            ║
║         ║                                                       ║░            ║
║         ║           [ Manage Aliases ]                         ║░            ║
║         ║                                                       ║░            ║
║         ║                                                       ║░            ║
║         ║                  [ Close ]                           ║░            ║
║         ║                                                       ║░            ║
║         ╚═══════════════════════════════════════════════════════╝░            ║
║           ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Idle                                                                           ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

The Options screen merges the former SET and SHOW commands into one unified interface:
- **Edit Settings**: Modify runtime configuration (formerly SET)
- **View Configuration**: Display current configuration (formerly SHOW)
- **Manage Aliases**: Add, edit, or remove command aliases

### 8. About Window (Help > About)

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ File  Edit  Run  Help                                     ChatrixCD v1.0      ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║      ╔════════════════════════════════════════════════════════════╗          ║
║      ║                   About ChatrixCD                       ║          ║
║      ╠════════════════════════════════════════════════════════════╣          ║
║      ║                                                            ║░         ║
║      ║  ChatrixCD                                                 ║░         ║
║      ║                                                            ║░         ║
║      ║  Matrix bot for CI/CD automation through chat            ║░         ║
║      ║                                                            ║░         ║
║      ║  Features:                                                ║░         ║
║      ║  • End-to-end encrypted Matrix rooms                     ║░         ║
║      ║  • Native Matrix authentication (password and OIDC/SSO)  ║░         ║
║      ║  • Interactive Text User Interface                       ║░         ║
║      ║  • Semaphore UI integration                              ║░         ║
║      ║  • Real-time task monitoring                             ║░         ║
║      ║                                                            ║░         ║
║      ║  License: GPL v3                                          ║░         ║
║      ║  Repository: github.com/CJFWeatherhead/ChatrixCD          ║░         ║
║      ║                                                            ║░         ║
║      ║                        [ OK ]                           ║░         ║
║      ║                                                            ║░         ║
║      ╚════════════════════════════════════════════════════════════╝░         ║
║        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░          ║
║                                                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ Idle                                                                           ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

The About window displays:
- Application name and description
- Key features list
- License information
- Repository link

## Menu Structure

### File Menu
- Status - View bot status
- Admins - View admin users
- Rooms - View joined rooms
- Exit - Quit application

### Edit Menu
- Sessions - Manage encryption sessions and device verification
- Options - Configuration management (merged SET and SHOW)
  - Edit Settings
  - View Configuration
  - Manage Aliases

### Run Menu
- Send - Send messages to rooms (formerly Say)

### Help Menu
- Show Log - View application logs
- About - Application information
- Version - Version and dependencies

## Implementation Details

The Turbo Vision-style TUI is implemented in `chatrixcd/tui_turbo.py` and features:

1. **TurboMenuBar**: Custom menu bar widget with F-key shortcuts
2. **TurboStatusBar**: Status bar showing idle/running task information
3. **TurboWindow**: Reusable window container with 3D borders and shadows
4. **Menu screens**: FileMenuScreen, EditMenuScreen, RunMenuScreen, HelpMenuScreen
5. **Modal dialogs**: StatusScreen, OptionsScreen, AboutScreen, VersionScreen

All screens reuse existing functionality from the original TUI while providing a more classic, windowed appearance inspired by Turbo Vision.

## Keyboard Shortcuts

- **F1**: Open File menu
- **F2**: Open Edit menu
- **F3**: Open Run menu
- **F4**: Open Help menu
- **Escape**: Close current screen/menu
- **Ctrl+C**: Quit application

## Status Bar States

The status bar at the bottom dynamically updates to show:
- **"Idle"**: No active tasks
- **"Running X task(s)"**: Number of currently running tasks
- **"X task(s) (idle)"**: Tasks tracked but not currently running

This provides at-a-glance information about the bot's activity without needing to open additional screens.
