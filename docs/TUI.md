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

## Advanced Features

### Real-Time Task Monitoring

The main menu now includes a real-time active tasks display that shows:

- All currently running Semaphore tasks
- Task IDs and project IDs
- Current status with color-coded indicators:
  - 🔄 **Running** (yellow)
  - ✅ **Success** (green)
  - ❌ **Error/Stopped** (red)
  - ⏸️ **Unknown/Pending** (blue)

The display updates automatically every 5 seconds, providing live feedback on CI/CD operations without needing to manually check task status.

```
Active Tasks

  🔄 Task 123 (Project 1): running
  ✅ Task 122 (Project 2): success
```

### Session Verification (Encryption)

The TUI now includes comprehensive device verification features for end-to-end encryption:

#### Emoji Verification

Full interactive emoji verification using the Matrix SDK:

1. Select "Verify Device (Emoji)" from the Sessions menu
2. Choose an unverified device from the list
3. The bot initiates SAS (Short Authentication String) verification
4. Compare the displayed emoji sequence (7 emojis) with the other device
5. If they match, click "✅ Yes, they match" to confirm verification
6. If they don't match, click "❌ No, they don't match" to reject
7. Upon confirmation, devices exchange and verify MAC codes automatically

**Features:**
- Uses Matrix SDK's native SAS verification protocol
- Real emoji sequences generated from shared secrets
- Automatic MAC exchange and verification
- Works with any Matrix client that supports emoji verification
- Permanent device verification (persisted across sessions)

#### QR Code Verification

Generate and scan QR codes for quick device verification:

1. Select "Verify Device (QR Code)" from the Sessions menu
2. A QR code is generated containing your device information
3. Scan with another device to verify your bot's identity
4. The QR code includes:
   - User ID
   - Device ID
   - Verification timestamp

#### Device Fingerprint

View and share your device's Ed25519 fingerprint for manual verification:

1. Select "Show Fingerprint" from the Sessions menu
2. Share the fingerprint with trusted parties
3. Use for out-of-band verification

#### Encryption Sessions List

View all active encryption sessions:

- User IDs and device IDs
- Device names
- Verification status (✅ verified / ⚠️ unverified)

### Interactive Configuration Editing

The SET menu now provides full interactive configuration editing:

#### Editable Variables

- **command_prefix**: Change the bot's command prefix (e.g., `!cd` to `!bot`)
- **greetings_enabled**: Enable/disable startup/shutdown messages
- **startup_message**: Customize the bot's startup greeting
- **shutdown_message**: Customize the bot's shutdown message

#### Edit Workflow

1. Select "SET - Change operational variables"
2. Choose a variable to edit
3. Enter the new value (with type validation)
4. Choose action:
   - **Apply Changes (Runtime Only)**: Changes take effect immediately but are lost on restart
   - **Save to config.json**: Changes are persisted to disk and survive restarts
   - **Discard Changes**: Abandon all pending modifications

#### Safety Features

- Type validation ensures correct data types
- Preview pending changes before applying
- Separate runtime and persistent save operations
- Graceful error handling with user-friendly messages

## Screenshots

### Main Menu with Active Tasks

```
╔═══════════════════════════════════════════════════════════════╗
║ ChatrixCD                                                     ║
╚═══════════════════════════════════════════════════════════════╝

                       ChatrixCD
            Matrix CI/CD Bot - Interactive Interface

Active Tasks

  🔄 Task 123 (Project 1): running
  ✅ Task 122 (Project 2): success

 ┌───────────────────────────────────────────────────────────┐
 │        STATUS - Show bot status                           │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │        SESSIONS - Session management                      │
 └───────────────────────────────────────────────────────────┘
 
 [Additional menu options...]
```

### Session Management Menu

```
╔═══════════════════════════════════════════════════════════════╗
║ ChatrixCD                                                     ║
╚═══════════════════════════════════════════════════════════════╝

                   Session Management

 ┌───────────────────────────────────────────────────────────┐
 │    View Encryption Sessions                               │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    Verify Device (Emoji)                                  │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    Verify Device (QR Code)                                │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    Show Fingerprint                                       │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    Reset Olm Sessions                                     │
 └───────────────────────────────────────────────────────────┘
```

### QR Code Verification

```
╔═══════════════════════════════════════════════════════════════╗
║ ChatrixCD                                                     ║
╚═══════════════════════════════════════════════════════════════╝

                  QR Code Verification

Scan this QR code with the other device:

████████████████████████████████
██          ██  ██  ██        ██
██  ██████  ██  ████  ██████  ██
██  ██████  ██      ██  ██  ████
██  ██████  ████████████  ██  ██
██          ██  ██  ██  ████  ██
████████████████████████████████

Device: ABCDEFGH
User: @chatrixcd:example.com

Note: The other device needs to scan this QR code
to verify this bot's identity.
```

### Configuration Editor

```
╔═══════════════════════════════════════════════════════════════╗
║ ChatrixCD                                                     ║
╚═══════════════════════════════════════════════════════════════╝

              Set Operational Variables

Select a variable to edit:

Bot Configuration:
 ┌───────────────────────────────────────────────────────────┐
 │    command_prefix                                         │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    greetings_enabled                                      │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    startup_message                                        │
 └───────────────────────────────────────────────────────────┘

Actions:
 ┌───────────────────────────────────────────────────────────┐
 │    Apply Changes (Runtime Only)                           │
 └───────────────────────────────────────────────────────────┘
 
 ┌───────────────────────────────────────────────────────────┐
 │    Save to config.json                                    │
 └───────────────────────────────────────────────────────────┘

Pending Changes:
  • command_prefix = !bot
  • greetings_enabled = false
```

## Future Enhancements

Additional features planned for future releases:

- Task history and logs viewer
- Performance metrics and graphs
- Dark/light theme toggle
- Custom color schemes
- Bulk device verification
- Advanced encryption session management
