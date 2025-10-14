---
layout: default
title: Quick Start
nav_order: 3
---

# Quick Start Guide

Get ChatrixCD up and running in minutes.

## 1. Install ChatrixCD

```bash
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 2. Create Configuration

Create a `config.json` file:

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
