# ChatrixCD Text User Interface (TUI)

## Overview

ChatrixCD includes a Text User Interface (TUI) that provides an interactive, menu-driven way to manage and monitor the bot. The TUI is built using the [Textual](https://textual.textualize.io/) framework and features:

- Menu-driven navigation
- Mouse support
- Brand colors (ChatrixCD green: #4A9B7F)
- Real-time status updates
- Log viewing
- Configuration display
- Room messaging

## Starting the TUI

The TUI launches automatically when running ChatrixCD in an interactive terminal:

```bash
chatrixcd
```

To enable colored output:

```bash
chatrixcd -C
```

To run without the TUI (classic log-only mode):

```bash
chatrixcd -L
```

## TUI Interface

### Main Menu

```
┌─────────────────────────────────────────────────────────────┐
│ ChatrixCD                                                   │
└─────────────────────────────────────────────────────────────┘

                        ChatrixCD
            Matrix CI/CD Bot - Interactive Interface

  ┌─────────────────────────────────────────────────────────┐
  │ STATUS - Show bot status                                │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ ADMINS - View admin users                               │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ ROOMS - Show joined rooms                               │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ SESSIONS - Session management                           │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ SAY - Send message to room                              │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ LOG - View log                                          │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ SET - Change operational variables                      │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ SHOW - Show current configuration                       │
  └─────────────────────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────────────────────┐
  │ QUIT - Exit                                             │
  └─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ q Quit                                                      │
└─────────────────────────────────────────────────────────────┘
```

## Menu Options

### STATUS

Displays real-time bot status information:

- **Matrix Connection**: Connected/Disconnected status
- **Semaphore Connection**: Connection status to Semaphore UI
- **Uptime**: How long the bot has been running
- **Messages Processed**: Total number of messages processed
- **Errors**: Count of errors encountered
- **Warnings**: Count of warnings logged

```
┌─────────────────────────────────────────────────────────────┐
│ ChatrixCD                                                   │
└─────────────────────────────────────────────────────────────┘

Bot Status

Matrix: Connected
Semaphore: Connected
Uptime: 2h 34m 12s

Metrics
Messages Processed: 147
Errors: 0
Warnings: 2

┌─────────────────────────────────────────────────────────────┐
│ escape Back                                                 │
└─────────────────────────────────────────────────────────────┘
```

### ADMINS

Lists all configured admin users:

```
Admin Users

  • @admin1:matrix.org
  • @admin2:example.com
  • @cicd-admin:company.org
```

### ROOMS

Shows all rooms the bot has joined:

```
Rooms

  • DevOps Team (!abcd1234:matrix.org)
  • CI/CD Notifications (!efgh5678:example.com)
  • Production Deploys (!ijkl9012:company.org)
```

### SESSIONS

Provides session management options:

- View Olm encryption sessions
- Reset Olm sessions (future feature)
- Verify sessions with other devices (future feature)

### SAY

Send a message from the bot to a room:

1. Select a room from dropdown
2. Type your message
3. Click "Send" button

```
Send Message

Select Room:
┌─────────────────────────────────────────────────────────────┐
│ Choose a room                                            ▼  │
└─────────────────────────────────────────────────────────────┘

Message:
┌─────────────────────────────────────────────────────────────┐
│ Type your message here...                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         Send                                │
└─────────────────────────────────────────────────────────────┘
```

### LOG

Displays the last 1000 lines of the bot log in a scrollable text area:

```
Log View

┌─────────────────────────────────────────────────────────────┐
│ 2025-10-12 01:15:23 - INFO - ChatrixCD starting...        │
│ 2025-10-12 01:15:24 - INFO - Connected to Matrix          │
│ 2025-10-12 01:15:25 - INFO - Joined room !abc:matrix.org  │
│ 2025-10-12 01:15:30 - INFO - Message from @user:matrix.org│
│ ...                                                          │
│                                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### SET

Change operational variables (future feature). Will allow modifying:

- Command prefix
- Greeting messages
- Admin users
- Allowed rooms

Changes can be applied immediately or saved to config.json.

### SHOW

Displays current configuration with sensitive credentials redacted:

```
Current Configuration

┌─────────────────────────────────────────────────────────────┐
│ {                                                            │
│   "matrix": {                                                │
│     "homeserver": "https://matrix.example.com",              │
│     "user_id": "@chatrixcd:example.com",                     │
│     "auth_type": "password",                                 │
│     "password": "***REDACTED***"                             │
│   },                                                         │
│   "semaphore": {                                             │
│     "url": "https://semaphore.example.com",                  │
│     "api_token": "***REDACTED***"                            │
│   },                                                         │
│   "bot": {                                                   │
│     "command_prefix": "!cd",                                 │
│     "admin_users": ["@admin:matrix.org"]                     │
│   }                                                          │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
```

### QUIT

Gracefully shuts down the bot:

1. Stops processing new messages
2. Sends shutdown message to greeting rooms (if configured)
3. Closes connections
4. Exits the TUI

## Keyboard Shortcuts

- **q** or **Ctrl+C**: Quit the TUI
- **Escape**: Go back to previous screen
- **Enter**: Select/activate button
- **Tab**: Navigate between elements
- **Arrow Keys**: Navigate menu items

## Mouse Support

The TUI fully supports mouse interaction:

- Click buttons to activate them
- Click menu items to select them
- Use scroll wheel to scroll through logs and lists
- Drag to select text (in log and config views)

## Color Support

When using the `-C` flag, the TUI displays in brand colors:

- **Header**: ChatrixCD green (#4A9B7F) background with white text
- **Footer**: Dark background (#2D3238)
- **Primary Buttons**: ChatrixCD green background
- **Text**: Standard terminal colors
- **Status**: Color-coded status indicators

Without the `-C` flag, the TUI remains fully functional using monochrome colors.

## System Requirements

- Python 3.8 or higher
- Terminal with support for:
  - UTF-8 encoding
  - ANSI escape sequences (for colors with `-C`)
  - Mouse events (optional, but recommended)

## Running Without TUI

To run ChatrixCD without the TUI (classic log-only mode):

```bash
chatrixcd -L
```

The TUI is automatically disabled when:

- Running in daemon mode (`-D`)
- Running in a non-interactive terminal (e.g., piped output)
- The `-L` or `--log-only` flag is used

## Troubleshooting

### TUI Not Starting

If the TUI doesn't start:

1. Ensure you're running in an interactive terminal
2. Check that the terminal supports ANSI escape sequences
3. Try running with `-L` flag to use log-only mode
4. Check for error messages in the log

### Display Issues

If the TUI displays incorrectly:

1. Resize your terminal window
2. Try running without colors (`chatrixcd` without `-C`)
3. Ensure your terminal is UTF-8 compatible
4. Check terminal size (minimum 80x24 recommended)

### Mouse Not Working

If mouse clicks don't work:

1. Use keyboard shortcuts instead (Tab, Enter, Arrow keys)
2. Check if your terminal emulator supports mouse events
3. Try a different terminal emulator

## Future Enhancements

Planned features for the TUI:

- Real-time task monitoring with status updates
- Session verification with QR codes and emojis
- Interactive configuration editing with validation
- Task history and logs
- Performance metrics and graphs
- Dark/light theme toggle
- Custom color schemes
