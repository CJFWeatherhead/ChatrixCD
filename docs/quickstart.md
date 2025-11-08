---
layout: default
title: Quick Start
nav_order: 3
---

# ⚡ Quick Start Guide

Get ChatrixCD up and running in **5 minutes**! 🚀

<div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 1em 0;">
  <strong>⏱️ Time to Success:</strong> ~5 minutes<br>
  <strong>📋 What You'll Need:</strong> Matrix account, Semaphore UI access, 5 minutes<br>
  <strong>🎯 What You'll Get:</strong> Fully working CI/CD bot in your chat!
</div>

---

## Step 1️⃣: Install ChatrixCD

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">📦 Pre-built Binary (Easiest!)</h3>
  <p><strong>✅ Recommended for most users</strong></p>
  <p>No Python required! Just download and run:</p>
  <pre><code>wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64
chmod +x chatrixcd-linux-x86_64
./chatrixcd-linux-x86_64</code></pre>
  <p><small>📖 <a href="installation.html#method-1-pre-built-binary-recommended">More download options →</a></small></p>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🔧 From Source (Advanced)</h3>
  <p><strong>For development or customization</strong></p>
  <pre><code>git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .</code></pre>
  <p><small>📖 <a href="installation.html#method-2-from-source">Full source guide →</a></small></p>
</div>

</div>

---

## Step 2️⃣: Create Configuration

Create a `config.json` file in the same directory as the binary (or project root if from source):

<div style="padding: 20px; background: #e7f3ff; border-left: 4px solid #2196F3; margin: 1em 0;">
  <strong>💡 Tip:</strong> Start with password auth for simplicity. You can switch to OIDC/SSO later!
</div>

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "password",
    "password": "your-secure-password",
    "device_name": "ChatrixCD Bot",
    "store_path": "./store"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-semaphore-api-token"
  },
  "bot": {
    "command_prefix": "!cd",
    "allowed_rooms": []
  }
}
```

## 3. Start the Bot

### From Binary

```bash
# Linux (adjust filename for your architecture)
./chatrixcd-linux-x86_64
# Or for other architectures:
# ./chatrixcd-linux-i686
# ./chatrixcd-linux-arm64
```

### From Source

```bash
chatrixcd
```

Or from source:

```bash
python -m chatrixcd.main
```

## 4. Invite Bot to Room

1. Create or open a Matrix room
2. Invite the bot: `/invite @bot:example.com`
3. The bot will automatically join

## 5. Use Bot Commands

Try these commands in your Matrix room:

### Get Help
```
!cd help
```

### List Projects
```
!cd projects
```

### List Templates
```
!cd templates 1
```

### Start a Task
```
!cd run 1 5
```

Replace `1` with your project ID and `5` with your template ID.

### Check Task Status
```
!cd status 123
```

Replace `123` with your task ID.

### Stop a Task
```
!cd stop 123
```

### Get Task Logs
```
!cd logs 123
```

## Example Workflow

Here's a complete workflow example:

```
User: !cd projects
Bot: Available projects:
     1. MyProject - Production deployment

User: !cd templates 1
Bot: Templates for project MyProject:
     5. Deploy to Production
     6. Run Tests

User: !cd run 1 5
Bot: ✅ Task started successfully
     Task ID: 123
     Project: MyProject
     Template: Deploy to Production

Bot: 🔄 Task 123 status: running

Bot: ✅ Task 123 completed successfully
```

## Advanced Configuration

### OIDC Authentication

For OIDC authentication with Matrix:

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "oidc",
    "oidc_issuer": "https://auth.example.com",
    "oidc_client_id": "your-client-id",
    "oidc_client_secret": "your-client-secret"
  }
}
```

## Next Steps

- [Full Configuration Guide](configuration.html)
- [Architecture Overview](architecture.html)
- [Deployment Options](deployment.html)
- [Contributing Guidelines](contributing.html)

## Troubleshooting

### Bot doesn't respond
- Check bot is running: look for log output
- Verify bot joined the room
- Check `allowed_rooms` configuration

### Authentication fails
- Verify credentials in config.json
- Check Matrix homeserver is accessible
- For OIDC, follow the SSO authentication flow

### Can't start tasks
- Verify Semaphore API token is valid
- Check Semaphore URL is correct and accessible
- Ensure project and template IDs exist

For more help, see the [Support Guide](support.html).
