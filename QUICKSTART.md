# Quick Start Guide

Get ChatrixCD up and running in 5 minutes!

## Installation

### Option 1: Pre-built Binary (Linux Only)

**No Python required!** Download and run:

**Linux (x86_64):**
```bash
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64
chmod +x chatrixcd-linux-x86_64
./chatrixcd-linux-x86_64
```

**Other Linux architectures:**
- **i686 (32-bit)**: [Download](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-i686)
- **ARM64**: [Download](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-arm64)

**Windows and macOS users:** Pre-built binaries are not currently available. Please use Option 2 (from source), Docker, or WSL2 (Windows only). See [INSTALL.md](INSTALL.md) for detailed platform-specific instructions.

### Option 2: From Source

If you prefer to build from source or need the latest development version:

```bash
# Prerequisites: Python 3.12+, uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv

# Clone the repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Install the bot
uv pip install -e .
```

## Configuration

**For binary users:** Create `config.json` in the same directory as the binary.

**For source users:** Create `config.json` in the repository root.

Configuration is done through JSON files (with HJSON support for comments).

### Quick Config (Password Authentication)

Create a `config.json` file:

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@chatrixcd:example.com",
    "auth_type": "password",
    "password": "your_bot_password"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your_api_token"
  },
  "bot": {
    "command_prefix": "!cd"
  }
}
```

### Alternative: OIDC/SSO Authentication

If your Matrix server uses OIDC/Single Sign-On:

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@chatrixcd:example.com",
    "auth_type": "oidc",
    "oidc_redirect_url": "http://localhost:8080/callback"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your_api_token"
  },
  "bot": {
    "command_prefix": "!cd"
  }
}
```

When you start the bot with OIDC:
1. It will display an SSO authentication URL
2. Open the URL in your browser
3. Complete authentication with your OIDC provider
4. Copy the callback URL (containing `loginToken`)
5. Paste it back into the bot

## Running the Bot

### From Binary

```bash
# Linux
./chatrixcd-linux-x86_64      # or your architecture's binary
# ./chatrixcd-linux-i686
# ./chatrixcd-linux-arm64
```

### From Source

**Interactive Mode (with TUI):**

By default, ChatrixCD starts with an interactive Text User Interface:

```bash
# Make sure your virtual environment is activated
# If not, activate it first:
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate    # On Windows

# Run the bot with TUI
chatrixcd

# Or with colored output
chatrixcd -C
```

The TUI provides a menu-driven interface with options for:
- **STATUS** - View bot status and metrics
- **ADMINS** - View admin users
- **ROOMS** - View joined rooms
- **SESSIONS** - Manage encryption sessions
- **SAY** - Send messages to rooms
- **LOG** - View bot logs
- **SET** - Change operational variables
- **SHOW** - View current configuration
- **QUIT** - Exit the bot

**Classic Log-Only Mode:**

To run without the TUI (shows only logs):

```bash
chatrixcd -L
```

The bot will:
1. Connect to your Matrix homeserver
2. Authenticate using your configured method
3. Start listening for commands

### Command-Line Options

For more control over the bot's behavior, use command-line options:

```bash
# Show help
chatrixcd --help

# Show version
chatrixcd --version

# Run with TUI and colored output
chatrixcd -C

# Run in classic log-only mode (no TUI)
chatrixcd -L

# Run with verbose logging (helpful for debugging)
chatrixcd -v -L

# Run with very verbose logging
chatrixcd -vv -L

# Use a custom config file
chatrixcd -c /path/to/config.json

# Run in daemon mode (background process, Unix/Linux only)
chatrixcd -D

# Display current configuration (credentials are hidden)
chatrixcd -s

# Override admin users and allowed rooms
chatrixcd -a @admin:matrix.org -r !room:matrix.org
```

## Using the Bot

1. **Invite the bot to a room**
   - Open your Matrix client
   - Invite `@chatrixcd:example.com` to your room
   - The bot will auto-join

2. **Test the bot**
   ```
   !cd help
   ```

3. **List available projects**
   ```
   !cd projects
   ```

4. **View templates for a project**
   ```
   !cd templates 1
   ```

5. **Start a task**
   ```
   !cd run 1 5
   ```
   This starts task from project 1, template 5

6. **Monitor task status**
   The bot automatically reports status updates!
   You can also check manually:
   ```
   !cd status 123
   ```

## Docker Quick Start

```bash
# Copy and edit configuration file
cp config.json.example config.json
nano config.json

# Update docker-compose.yml to mount config.json (uncomment the config volume line)

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f chatrixcd
```

## Troubleshooting

### Bot doesn't start

Check your configuration:
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # On Linux/macOS
python -c "from chatrixcd.config import Config; c = Config(); print(c.get_matrix_config())"
```

### Can't connect to Matrix

- Verify homeserver URL is correct
- Check credentials are valid
- Ensure network connectivity

### Can't connect to Semaphore

- Verify Semaphore URL is accessible
- Check API token is valid
- Test with: `curl -H "Authorization: Bearer YOUR_TOKEN" https://semaphore.example.com/api/projects`

### Bot doesn't respond to commands

- Check the command prefix (default: `!cd`)
- Verify bot has joined the room
- Check bot logs for errors

## Next Steps

- Read [INSTALL.md](INSTALL.md) for detailed installation options
- Review [README.md](README.md) for full documentation
- Configure access controls with `allowed_rooms` and `admin_users`

## Getting Help

- Check the logs: `tail -f chatrixcd.log`
- Review error messages in the Matrix room
- Open an issue on GitHub

## Example Session

```
User: !cd help
Bot: **ChatrixCD Bot Commands**
     !cd help - Show this help message
     !cd projects - List available projects
     ...

User: !cd projects
Bot: **Available Projects:**
     • My Web App (ID: 1)
     • Database Backup (ID: 2)

User: !cd templates 1
Bot: **Templates for Project 1:**
     • Deploy to Production (ID: 5)
     • Run Tests (ID: 6)

User: !cd run 1 5
Bot: Starting task from template 5...
     ✅ Task 123 started successfully!
     Use '!cd status 123' to check progress.

[10 seconds later]
Bot: 🔄 Task 123 is now running...

[2 minutes later]
Bot: ✅ Task 123 completed successfully!
```

Happy automating! 🚀
