# ChatrixCD Customization Guide

This guide explains how to customize ChatrixCD's behavior through configuration files.

## Table of Contents

- [Message Customization](#message-customization)
- [Command Aliases](#command-aliases)
- [Configuration](#configuration)
- [Hot-Reload Feature](#hot-reload-feature)

## Message Customization

ChatrixCD's personality and responses can be fully customized without changing any code!

### Getting Started

1. **Copy the example file**:
   ```bash
   cp messages.json.example messages.json
   ```

2. **Edit `messages.json`** to customize bot responses

3. **Start the bot** - it will use your custom messages

### Message Categories

The `messages.json` file contains several categories of responses:

#### Greetings
Used when addressing users:
```json
"greetings": [
  "{name} 👋",
  "Hi {name}! 👋",
  "Hello {name}! 😊"
]
```

The `{name}` placeholder is replaced with the user's display name.

#### Brush-Off Messages
Used when non-admin users try to run commands:
```json
"brush_off": [
  "I can't talk to you 🫢 (Admin vibes only!)",
  "You're not my boss 🫠 ...unless you're an admin?"
]
```

#### Cancellation Messages
Used when tasks are cancelled:
```json
"cancel": [
  "Task execution cancelled. No problem! ❌ We cool!",
  "Cancelled! Maybe another time. 👋 I'll be here!"
]
```

#### Timeout Messages
Used when confirmations expire:
```json
"timeout": [
  "I'll just go back to what I was doing then? 🙄",
  "Timeout! Maybe next time? ⏰"
]
```

#### Task Start Messages
Used when starting a task:
```json
"task_start": [
  "On it! Starting **{task_name}**... 🚀",
  "Here we go! Running **{task_name}**... 🏃"
]
```

The `{task_name}` placeholder is replaced with the template name.

#### Ping Success Messages
Used when pinging Semaphore server:
```json
"ping_success": [
  "{user_name} 👋 - 🏓 Semaphore server is alive and kicking! ✅",
  "{user_name} 👋 - 🏓 Pong! Server is up! ✅"
]
```

#### Pet Messages (Easter Egg)
Used for the secret `!cd pet` command:
```json
"pet": [
  "Aww, thanks {user_name}! 🥰 *happy bot noises*",
  "{user_name}, you're the best! 😊 *purrs digitally*"
]
```

#### Scold Messages (Easter Egg)
Used for the secret `!cd scold` command:
```json
"scold": [
  "Oh no, {user_name}! 😢 I'll try harder, I promise!",
  "Sorry {user_name}... 😔 What did I do wrong?"
]
```

### Customization Tips

1. **Keep variety**: Add multiple messages per category for unpredictable responses
2. **Use emojis**: Emojis make responses more engaging and fun
3. **Include placeholders**: Use `{name}`, `{user_name}`, or `{task_name}` where appropriate
4. **Maintain tone**: Keep messages consistent with the bot's personality
5. **Test changes**: The bot reloads messages automatically - no restart needed!

### Example Customization

To create a more professional bot, you might change:

```json
{
  "greetings": [
    "Hello {name}",
    "Good day {name}"
  ],
  "cancel": [
    "Task cancelled.",
    "Operation cancelled."
  ],
  "task_start": [
    "Starting task: {task_name}",
    "Executing: {task_name}"
  ]
}
```

## Command Aliases

Create shortcuts for frequently used commands with `aliases.json`.

### Getting Started

1. **Copy the example file**:
   ```bash
   cp aliases.json.example aliases.json
   ```

2. **Add your aliases**:
   ```json
   {
     "p": "projects",
     "t": "templates",
     "r": "run",
     "s": "status",
     "deploy": "run 1 5"
   }
   ```

3. **Use aliases** just like regular commands:
   ```
   !cd p          → Lists projects
   !cd deploy     → Runs project 1, template 5
   ```

### Alias Rules

- **Cannot override** built-in commands (help, projects, run, etc.)
- **Can include arguments**: `"deploy": "run 1 5"`
- **Can chain**: Alias can reference another alias
- **Auto-reload**: Changes take effect automatically

### Example Aliases

```json
{
  "p": "projects",
  "t": "templates",
  "s": "status",
  "l": "logs",
  "prod-deploy": "run 1 3",
  "staging-deploy": "run 1 4",
  "check": "status"
}
```

## Configuration

The main bot configuration is in `config.json`.

### Getting Started

1. **Initialize config**:
   ```bash
   chatrixcd --init
   ```
   
   Or copy the example:
   ```bash
   cp config.json.example config.json
   ```

2. **Edit configuration**:
   ```json
   {
     "matrix": {
       "homeserver": "https://matrix.org",
       "user_id": "@bot:matrix.org",
       "auth_type": "password",
       "password": "your-password"
     },
     "semaphore": {
       "url": "https://semaphore.example.com",
       "api_token": "your-api-token"
     },
     "bot": {
       "command_prefix": "!cd",
       "admin_users": ["@admin:matrix.org"],
       "allowed_rooms": []
     }
   }
   ```

3. **Start the bot** with your configuration

### Key Settings

#### Matrix Configuration
- `homeserver`: Your Matrix homeserver URL
- `user_id`: Bot's Matrix user ID
- `auth_type`: "password" or "oidc"
- `password`: Bot's password (for password auth)

#### Semaphore Configuration
- `url`: Semaphore UI URL
- `api_token`: Semaphore API token

#### Bot Configuration
- `command_prefix`: Command prefix (default: "!cd")
- `admin_users`: List of admin user IDs
- `allowed_rooms`: List of allowed room IDs (empty = all rooms)
- `greetings_enabled`: Enable/disable startup/shutdown messages
- `greeting_rooms`: Rooms to send greetings to

## Hot-Reload Feature

All configuration files support **hot-reload** - changes take effect without restarting the bot!

### How It Works

The bot automatically monitors configuration files:
- `config.json` - Checked every 10 seconds
- `aliases.json` - Checked every 5 seconds
- `messages.json` - Checked every 5 seconds

When a file is modified, the bot:
1. Detects the change
2. Reloads the file
3. Applies the changes immediately
4. Logs the reload event

### Benefits

- **No downtime**: Update config without restarting
- **Rapid testing**: Try different messages instantly
- **Easy debugging**: Adjust settings while troubleshooting
- **Graceful updates**: Changes apply smoothly

### What Gets Reloaded?

| File | Reloads | Notes |
|------|---------|-------|
| `messages.json` | All bot responses | Takes effect immediately |
| `aliases.json` | Command shortcuts | New aliases available instantly |
| `config.json` | Most settings | Some settings require restart¹ |

¹ Matrix authentication settings (homeserver, user_id, auth_type) require a restart because they affect the Matrix client initialization.

### Testing Hot-Reload

1. **Start the bot**:
   ```bash
   chatrixcd
   ```

2. **Modify a file** (e.g., add a greeting to `messages.json`):
   ```json
   {
     "greetings": [
       "Howdy {name}! 🤠",
       "NEW GREETING {name}! 🎉"
     ]
   }
   ```

3. **Trigger the greeting** with a command:
   ```
   !cd help
   ```

4. **See the new message** - no restart needed!

### Monitoring Reloads

Check the bot logs to see when files are reloaded:

```
2025-10-24 10:30:15 - chatrixcd.messages - INFO - Messages file 'messages.json' has been modified, reloading...
2025-10-24 10:30:15 - chatrixcd.messages - INFO - Loaded messages from 'messages.json'
```

## Troubleshooting

### Messages Not Loading

**Problem**: Custom messages aren't being used

**Solutions**:
1. Check file name is exactly `messages.json`
2. Verify JSON syntax (use a JSON validator)
3. Check bot logs for parsing errors
4. Ensure file is in the same directory as the bot

### Aliases Not Working

**Problem**: Alias doesn't execute

**Solutions**:
1. Check alias doesn't conflict with built-in command
2. Verify JSON syntax in `aliases.json`
3. Check bot logs for errors
4. Try reloading manually by modifying the file

### Hot-Reload Not Working

**Problem**: Changes aren't detected

**Solutions**:
1. Wait 5-10 seconds (check interval)
2. Verify file was actually saved
3. Check file permissions
4. Look for errors in bot logs

### JSON Syntax Errors

**Problem**: File won't load after editing

**Solutions**:
1. Use a JSON validator (e.g., jsonlint.com)
2. Check for:
   - Missing commas
   - Unclosed brackets
   - Unquoted strings
   - Invalid escape sequences
3. Revert to a backup if needed
4. Use HJSON format (allows comments and trailing commas)

## Best Practices

1. **Backup before editing**: Keep copies of working configurations
2. **Test in development**: Try changes in a test environment first
3. **Use version control**: Track configuration changes with Git
4. **Document custom messages**: Comment your message categories
5. **Keep it consistent**: Maintain similar tone across all messages
6. **Monitor logs**: Watch for reload confirmations and errors

## Examples

### Professional Bot

```json
{
  "greetings": [
    "Hello {name}",
    "Greetings {name}"
  ],
  "brush_off": [
    "Access denied. Admin privileges required.",
    "Unauthorized. Please contact an administrator."
  ],
  "cancel": [
    "Task cancelled.",
    "Operation cancelled."
  ],
  "task_start": [
    "Starting task: {task_name}",
    "Executing: {task_name}"
  ]
}
```

### Casual Bot

```json
{
  "greetings": [
    "Yo {name}! What's up? 😎",
    "Hey {name}! Ready to deploy? 🚀"
  ],
  "brush_off": [
    "Whoa there! Admins only, buddy! 🚫",
    "Nice try! But you need admin powers! 💪"
  ],
  "cancel": [
    "No worries! Cancelled that for ya! ✌️",
    "Alright, stopping that! All good! 👍"
  ],
  "task_start": [
    "Let's gooo! Starting {task_name}! 🔥",
    "On it! {task_name} is launching! 🎯"
  ]
}
```

### Minimal Bot

```json
{
  "greetings": ["{name}"],
  "brush_off": ["Access denied."],
  "cancel": ["Cancelled."],
  "task_start": ["Starting {task_name}."]
}
```

## Further Reading

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Bot architecture overview
- [CONCURRENT_ARCHITECTURE.md](../CONCURRENT_ARCHITECTURE.md) - Concurrent execution details
- [README.md](../README.md) - General bot usage
- [INSTALL.md](../INSTALL.md) - Installation guide
