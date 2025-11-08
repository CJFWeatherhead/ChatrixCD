# Quick Start Guide

Get ChatrixCD running in minutes! 🚀

## 1. Install

### Linux (Binary - Easiest!)
```bash
# Download and extract (replace x86_64 with i686 or arm64 if needed)
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist
```

### From Source (All Platforms)
```bash
# Prerequisites: Python 3.12+
pip install -e .
```

**Need more details?** See [INSTALL.md](INSTALL.md)

## 2. Configure

Create `config.json`:
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
  }
}
```

**Configuration options:** [Configuration Guide](https://chatrixcd.cjfw.me/configuration.html)

## 3. Run

```bash
./chatrixcd              # Linux binary
# OR
chatrixcd                # From source
```

The bot will:
- Connect to your Matrix server
- Join rooms you invite it to
- Wait for commands

## 4. Use It!

Invite your bot to a Matrix room, then:

```
!cd help                    # Show available commands
!cd projects                # List your CI/CD projects
!cd templates 1             # Show templates for project 1
!cd run 1 5                 # Run template 5 in project 1
!cd status                  # Check task status
!cd logs                    # View task logs
```

**React with 👍** to confirm actions or **👎** to cancel!

## Common Tasks

### Create Command Aliases
```
!cd alias add deploy "run 1 5"
!cd alias deploy              # Now this runs template 5!
```

### Monitor Tasks
```
!cd log on                    # Enable auto log streaming
!cd status                    # Check running tasks
!cd stop 123                  # Stop task 123
```

### Manage the Bot
```
!cd admins list               # Show admin users
!cd rooms list                # Show allowed rooms
```

## Troubleshooting

**Bot not responding?**
- Check it's in the room: Invite `@mybot:matrix.org`
- Verify room is in `allowed_rooms` config
- Check logs with `-v` flag: `chatrixcd -v`

**OIDC/SSO Authentication?**
- Set `"auth_type": "oidc"` in config
- Bot will show login URL when starting
- See [Authentication Guide](https://chatrixcd.cjfw.me/configuration.html#authentication)

**E2E Encrypted rooms?**
- Bot automatically handles encryption
- First message may ask for device verification
- Use TUI mode (`chatrixcd` without `-L`) for easier verification

## Next Steps

- 📚 [Full Documentation](https://chatrixcd.cjfw.me/)
- 🔧 [Configuration Reference](https://chatrixcd.cjfw.me/configuration.html)
- 🎨 [Customize Messages](https://chatrixcd.cjfw.me/customization.html)
- 🏗️ [Architecture Details](https://chatrixcd.cjfw.me/architecture.html)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

---

**Questions?** Check the [Support page](SUPPORT.md) or [open an issue](https://github.com/CJFWeatherhead/ChatrixCD/issues)!
