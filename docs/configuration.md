---
layout: default
title: Configuration
nav_order: 4
---

# Configuration Guide

ChatrixCD can be configured using YAML files or environment variables.

## Configuration Priority

Configuration is loaded in this order (later sources override earlier ones):

1. Default values (hardcoded)
2. YAML configuration file (`config.yaml`)
3. Environment variables

## YAML Configuration

Create a `config.yaml` file in your working directory:

```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  password: "your-secure-password"
  device_name: "ChatrixCD Bot"
  store_path: "./store"
  
semaphore:
  url: "https://semaphore.example.com"
  api_token: "your-semaphore-api-token"
  
bot:
  command_prefix: "!cd"
  allowed_rooms: []
```

## Environment Variables

Environment variables use `SCREAMING_SNAKE_CASE` with component prefixes:

### Matrix Configuration

- `MATRIX_HOMESERVER` - Matrix homeserver URL (required)
- `MATRIX_USER_ID` - Bot user ID, e.g., `@bot:example.com` (required)
- `MATRIX_PASSWORD` - Bot password (required if not using token/OIDC)
- `MATRIX_ACCESS_TOKEN` - Pre-generated access token (alternative to password)
- `MATRIX_DEVICE_NAME` - Device name for the bot (default: "ChatrixCD Bot")
- `MATRIX_STORE_PATH` - Path to store encryption keys (default: "./store")
- `MATRIX_AUTH_TYPE` - Authentication type: "password", "token", or "oidc" (default: "password")

### OIDC Configuration

For OIDC authentication:

- `MATRIX_OIDC_CLIENT_ID` - OIDC client ID
- `MATRIX_OIDC_CLIENT_SECRET` - OIDC client secret
- `MATRIX_OIDC_ISSUER` - OIDC issuer URL
- `MATRIX_OIDC_REDIRECT_URI` - OIDC redirect URI (optional)

### Semaphore Configuration

- `SEMAPHORE_URL` - Semaphore UI URL (required)
- `SEMAPHORE_API_TOKEN` - Semaphore API token (required)

### Bot Configuration

- `BOT_COMMAND_PREFIX` - Command prefix (default: "!cd")
- `BOT_ALLOWED_ROOMS` - Comma-separated list of allowed room IDs (empty = all rooms)
- `BOT_GREETINGS_ENABLED` - Enable/disable startup and shutdown messages (default: "true")
- `BOT_GREETING_ROOMS` - Comma-separated list of room IDs to send greetings to (empty = no greetings)
- `BOT_STARTUP_MESSAGE` - Custom startup message (default: "🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!")
- `BOT_SHUTDOWN_MESSAGE` - Custom shutdown message (default: "👋 ChatrixCD bot is shutting down. See you later!")

## Authentication Methods

### Password Authentication

```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  password: "your-password"
  auth_type: "password"
```

### Token Authentication

```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  access_token: "your-access-token"
  auth_type: "token"
```

### OIDC Authentication

```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  auth_type: "oidc"
  oidc:
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    issuer: "https://auth.example.com"
```

## Access Control

### Allow All Rooms

```yaml
bot:
  allowed_rooms: []
```

### Restrict to Specific Rooms

```yaml
bot:
  allowed_rooms:
    - "!roomid1:example.com"
    - "!roomid2:example.com"
```

## Example Configurations

### Development Setup

```yaml
matrix:
  homeserver: "https://matrix.org"
  user_id: "@mybot:matrix.org"
  password: "dev-password"
  device_name: "ChatrixCD Dev"
  store_path: "./dev-store"

semaphore:
  url: "http://localhost:3000"
  api_token: "dev-token"

bot:
  command_prefix: "!cd"
  allowed_rooms: []
```

### Production Setup with OIDC

```yaml
matrix:
  homeserver: "https://matrix.company.com"
  user_id: "@cicd-bot:company.com"
  auth_type: "oidc"
  oidc:
    client_id: "${OIDC_CLIENT_ID}"
    client_secret: "${OIDC_CLIENT_SECRET}"
    issuer: "https://auth.company.com"
  device_name: "ChatrixCD Production"
  store_path: "/var/lib/chatrixcd/store"

semaphore:
  url: "https://semaphore.company.com"
  api_token: "${SEMAPHORE_API_TOKEN}"

bot:
  command_prefix: "!cd"
  allowed_rooms:
    - "!devops:company.com"
    - "!ci-alerts:company.com"
  greetings_enabled: true
  greeting_rooms:
    - "!devops:company.com"
  startup_message: "🚀 CI/CD Bot online!"
  shutdown_message: "🛑 CI/CD Bot going offline for maintenance"
```

### Greeting Messages Configuration

You can configure the bot to send startup and shutdown messages to specific rooms:

```yaml
bot:
  # Enable or disable greeting messages globally
  greetings_enabled: true
  
  # Specify which rooms should receive greeting messages
  # Leave empty to disable greetings
  greeting_rooms:
    - "!roomid1:example.com"
    - "!roomid2:example.com"
  
  # Customize startup message
  startup_message: "🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!"
  
  # Customize shutdown message
  shutdown_message: "👋 ChatrixCD bot is shutting down. See you later!"
```

**Note:** Greeting messages are only sent to rooms explicitly listed in `greeting_rooms`. This allows you to control which rooms receive these notifications, which is especially useful if the bot is in many rooms but you only want status updates in specific ones.

To disable greetings entirely, either:
- Set `greetings_enabled: false`, or
- Leave `greeting_rooms` empty, or
- Set environment variable `BOT_GREETINGS_ENABLED=false`

## Security Best Practices

### Protect Configuration Files

```bash
chmod 600 config.yaml
chmod 700 store/
```

### Use Environment Variables in Production

Instead of storing secrets in YAML:

```bash
export MATRIX_PASSWORD="$(cat /secrets/matrix_password)"
export SEMAPHORE_API_TOKEN="$(cat /secrets/semaphore_token)"
```

### Rotate Credentials Regularly

- Change bot password periodically
- Regenerate API tokens regularly
- Update access tokens when needed

## Troubleshooting

### Configuration not loaded
- Check file name is exactly `config.yaml`
- Verify YAML syntax is valid - the bot will display detailed error messages if the YAML is malformed, including:
  - Line and column number of the error
  - Description of the problem (e.g., missing quote, invalid indentation)
  - Context of where the error occurred
- Check file permissions

### Environment variables not working
- Ensure variables are exported
- Check variable names match exactly
- Verify no typos in variable names

### Authentication fails
- Verify credentials are correct
- Check homeserver URL is accessible
- For OIDC, verify client credentials

For more help, see the [Support Guide](support.html).
