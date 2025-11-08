# Installation Guide

Choose your installation method and get ChatrixCD running quickly! 🚀

## Installation Methods

| Method | Best For | Difficulty |
|--------|----------|------------|
| **Pre-built Binary** | Linux users wanting the easiest setup | ⭐ Easy |
| **From Source** | Development, Windows, macOS | ⭐⭐ Moderate |
| **Docker** | Containerized deployments | ⭐⭐ Moderate |

## Method 1: Pre-built Binary (Linux)

**Features:** No Python needed, fully static, works on any Linux distro

### Install

```bash
# Download (replace x86_64 with i686 or arm64 for other architectures)
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist

# Run
./chatrixcd
```

**Available:** [x86_64](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz) | [i686](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-i686.dist.tar.gz) | [ARM64](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-arm64.dist.tar.gz)

**Windows/macOS:** Binaries not available - use Method 2 or Docker

## Method 2: From Source

### Prerequisites

- **Python 3.12 or newer**
- **Git** (to clone the repository)

### Install

```bash
# Clone repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Install
pip install -e .

# Run
chatrixcd
```

**Platform-specific notes:**
- **Windows:** Works natively with Python 3.12+
- **macOS:** Install Python 3.12+ via Homebrew: `brew install python@3.12`
- **Linux:** Most distros have Python 3.12+ in repos

## Method 3: Docker

### Using Docker Compose (Recommended)

Create `docker-compose.yml`:
```yaml
services:
  chatrixcd:
    image: ghcr.io/cjfweatherhead/chatrixcd:latest
    volumes:
      - ./config.json:/app/config.json:ro
      - ./store:/app/store
    restart: unless-stopped
```

Run:
```bash
docker compose up -d
```

### Using Docker CLI

```bash
docker run -d \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/store:/app/store \
  --name chatrixcd \
  ghcr.io/cjfweatherhead/chatrixcd:latest
```

## Configuration

Create `config.json` in your installation directory:

```json
{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@mybot:matrix.org",
    "auth_type": "password",
    "password": "your-password"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token"
  },
  "bot": {
    "command_prefix": "!cd",
    "admin_users": ["@you:matrix.org"],
    "allowed_rooms": []
  }
}
```

**Configuration options:** See [Configuration Reference](https://chatrixcd.cjfw.me/configuration.html)

### Authentication Options

**Password Authentication (Simple):**
```json
{
  "matrix": {
    "auth_type": "password",
    "password": "your-password"
  }
}
```

**OIDC/SSO Authentication:**
```json
{
  "matrix": {
    "auth_type": "oidc",
    "oidc_redirect_url": "http://localhost:8080"
  }
}
```

The bot will display a login URL when starting.

### Getting Semaphore API Token

1. Log into Semaphore UI
2. Click your profile (top right)
3. Go to **API Keys**
4. Create new key
5. Copy token to `config.json`

## Running the Bot

### Basic Usage

```bash
chatrixcd                    # Run with TUI (default)
chatrixcd -L                 # Log-only mode (no TUI)
chatrixcd -D                 # Daemon mode (background)
chatrixcd -v                 # Verbose logging
```

### System Service (Linux)

**systemd service** (`/etc/systemd/system/chatrixcd.service`):
```ini
[Unit]
Description=ChatrixCD Matrix Bot
After=network-online.target

[Service]
Type=simple
User=chatrixcd
WorkingDirectory=/opt/chatrixcd
ExecStart=/opt/chatrixcd/chatrixcd -L
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable --now chatrixcd
```

**Alpine Linux (OpenRC)** (`/etc/init.d/chatrixcd`):
```bash
#!/sbin/openrc-run
command="/opt/chatrixcd/chatrixcd"
command_args="-L"
command_user="chatrixcd:chatrixcd"
directory="/opt/chatrixcd"
```

## Verification

### Test the Bot

1. **Invite bot to room:** Send invite to your bot's Matrix ID
2. **Send test command:** `!cd help`
3. **Check response:** Bot should reply with help message

### Device Verification (E2E Encryption)

If using encrypted rooms:

1. Bot will prompt for device verification
2. **With TUI:** Use interactive verification screen
3. **Without TUI:** Use emoji verification in logs
4. **Or:** Use `!cd verify` command in room

## Troubleshooting

### Bot Won't Start

**"No config file found"**
- Create `config.json` in the same directory as the binary/script

**"Failed to connect to Matrix server"**
- Check `homeserver` URL is correct
- Verify network connectivity
- Check firewall settings

**"Authentication failed"**
- Verify `user_id` and `password` are correct
- For OIDC: Complete browser login when prompted

### Bot Not Responding

**Bot joined but silent:**
- Check room is in `allowed_rooms` (or leave empty to allow all)
- Verify bot user is in `admin_users` for admin commands
- Check logs with `chatrixcd -v`

**"Permission denied" errors:**
- Verify bot account has permission to send messages
- Check room power levels

### Common Issues

**Import errors (from source):**
```bash
pip install --upgrade pip
pip install -e .
```

**Binary "Permission denied":**
```bash
chmod +x chatrixcd-linux-*
```

**Port already in use (OIDC):**
- Change `oidc_redirect_url` to different port
- Or use password authentication

## Next Steps

- 📖 [Quick Start Guide](QUICKSTART.md) - Get running in 5 minutes
- ⚙️ [Configuration Reference](https://chatrixcd.cjfw.me/configuration.html) - All config options
- 🎨 [Customization Guide](https://chatrixcd.cjfw.me/customization.html) - Customize messages and aliases
- 📚 [Full Documentation](https://chatrixcd.cjfw.me/) - Complete docs

## Getting Help

- 📝 [Support Guide](SUPPORT.md)
- 🐛 [Issue Tracker](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- 💬 [Discussions](https://github.com/CJFWeatherhead/ChatrixCD/discussions)
