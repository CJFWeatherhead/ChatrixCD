# Runtime Metrics and Enhanced Commands

This document describes the runtime metrics tracking and enhanced command features added to ChatrixCD.

## Runtime Metrics

The bot now tracks the following runtime metrics:

- **Messages Sent**: Total number of messages sent by the bot
- **Requests Received**: Total number of commands received from users
- **Errors**: Total number of errors encountered (not yet implemented for tracking)
- **Emojis Used**: Total number of emojis used in bot messages and reactions

### Implementation Details

Metrics are stored in `bot.metrics` dictionary and are tracked automatically:

- `send_message()` increments `messages_sent` and counts emojis in the message
- `send_reaction()` increments `emojis_used` 
- `message_callback()` increments `requests_received` when a command is detected

### Emoji Counting

The bot uses a Unicode regex pattern to detect and count emojis across multiple ranges:
- Emoticons (😊, 😂, etc.)
- Symbols & Pictographs (🎉, 🎊, etc.)
- Transport & Map Symbols (🚀, 🚗, etc.)
- Flags (🇺🇸, 🇬🇧, etc.)
- Dingbats (✅, ❌, etc.)

Note: Consecutive emojis are matched as a group but counted individually.

## Enhanced !cd info Command

The `!cd info` command now displays:

### System Information
- **CPU Model**: Processor model name (e.g., "Intel Core i7-4770K")
  - Detected on Linux (from `/proc/cpuinfo`)
  - Detected on macOS (from `sysctl`)
  - Detected on Windows (from `wmic`)
- **Runtime Type**: 
  - "Binary (compiled)" for frozen executables
  - "Python X.X.X (interpreter)" for source installations

### Runtime Metrics
- Messages Sent
- Requests Received
- Errors
- Emojis Used

### Display Format
Information is displayed in both:
- Plain text with bullet points
- HTML tables for Matrix clients that support rich formatting

## Enhanced !cd rooms Command

The `!cd rooms` command now includes:

### Send Permission Detection
- Bot checks if it can send messages in each room based on:
  - Room membership
  - Power levels (user level vs required level for m.room.message)

### Color Coding
- **Green (✅)**: Bot can send messages in the room
- **Red (❌)**: Bot cannot send messages in the room

### Redaction Mode
When the `-R` (redaction) flag is set:
- Rooms where the bot cannot send messages are hidden from the list
- This prevents leaking information about rooms the bot is in but cannot interact with

### Table Format
Rooms are displayed in an HTML table with columns:
- Room Name
- Room ID
- Send Status (Can send / Cannot send)

## Version Detection with Git

### Automatic Commit ID

When running from a git repository (not a release), the bot automatically appends the short commit hash to the version:

- **Release**: `2025.11.15.5.2.0`
- **Git**: `2025.11.15.5.2.0-cb105d9b`

### Implementation

The `_get_version_with_commit()` function in `__init__.py`:
1. Checks if `.git` directory exists
2. Runs `git rev-parse --short HEAD` to get commit hash
3. Appends `-c<hash>` to the version string
4. Exports as `__version_full__`

### Display Locations

The full version (with commit if applicable) is displayed in:
- `!cd info` command output
- `-V` / `--version` CLI flag
- TUI status display (once implemented)
- Startup log messages

## TUI Harmonization

The TUI status widget has been updated to match the `!cd info` command:

### Old Metrics (Removed)
- messages_processed
- warnings

### New Metrics (Aligned with Commands)
- messages_sent
- requests_received
- errors
- emojis_used

The TUI now reads metrics directly from `bot.metrics` for consistency.

## Testing

Unit tests are provided in `tests/test_metrics_and_version.py`:

- `TestVersionDetection`: Tests version format and git commit detection
- `TestMetricsStructure`: Tests metrics dictionary structure
- `TestEmojiCounting`: Tests emoji detection and counting logic

Run tests with:
```bash
python3 -m unittest tests.test_metrics_and_version
```

## Future Enhancements

Potential improvements:
- Error tracking implementation
- Metrics persistence across restarts
- Metrics reset command
- Historical metrics (per-session, per-day)
- Metrics export/reporting
