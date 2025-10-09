---
layout: default
title: Configuration
nav_order: 4
---

# Configuration Guide

ChatrixCD can be configured using YAML files, JSON files, or environment variables.

## Supported Configuration Formats

ChatrixCD supports two configuration file formats:

1. **YAML** (`.yaml` or `.yml`) - Human-readable, but syntax-sensitive
2. **JSON** (`.json`) - More robust parsing, less prone to syntax errors

The format is automatically detected based on the file extension. JSON is recommended for production deployments due to its more robust parsing and better error detection.

## Configuration Versioning

Configuration files support versioning to enable automatic migration when new features are added. The current configuration version is **2**.

When you load an older configuration file:
- It will be automatically migrated to the current version
- A backup of the original file is created (with `.backup` extension)
- The migrated configuration is saved back to the original file
- All your settings are preserved during migration

### Version History

- **Version 1** (implicit): Original configuration format
- **Version 2**: Added greeting messages support (`greetings_enabled`, `greeting_rooms`, `startup_message`, `shutdown_message`)

## Configuration Priority

Configuration values are determined using the following priority (highest to lowest):

1. **YAML configuration file** (`config.yaml`) - explicit values in the YAML file take highest priority
2. **Environment variables** - used as defaults when YAML doesn't specify a value
3. **Default values** (hardcoded) - used when neither YAML nor environment variables specify a value

**Example:** If your `config.yaml` has `user_id` but not `device_id`, and you set the `MATRIX_DEVICE_ID` environment variable, then:
- `user_id` will come from the YAML file
- `device_id` will come from the environment variable
- Other unspecified fields (like `device_name`) will use hardcoded defaults

## YAML Configuration

Create a `config.yaml` file in your working directory:

```yaml
# Configuration version (optional, for automatic migration)
_config_version: 2

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

## JSON Configuration

Alternatively, create a `config.json` file for more robust parsing:

```json
{
  "_config_version": 2,
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
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

**Benefits of JSON:**
- More robust syntax (no indentation issues)
- Better error messages with line and column numbers
- Easier to generate programmatically
- Less prone to quoting and escaping errors

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

## Configuration Validation

ChatrixCD includes built-in configuration validation to catch errors early. The validation checks:

- Required fields are present (homeserver, user_id, etc.)
- Authentication configuration is complete for the chosen auth_type
- Semaphore URL and API token are set
- Bot command prefix is configured

Validation errors will be reported with clear messages indicating which fields need attention.

## Troubleshooting

### Configuration not loaded
- Check file name is exactly `config.yaml` or `config.json`
- For YAML: Verify YAML syntax is valid - the bot will display detailed error messages if the YAML is malformed, including:
  - Line and column number of the error
  - Description of the problem (e.g., missing quote, invalid indentation)
  - Context of where the error occurred
- For JSON: Verify JSON syntax is valid - parse errors will show exact line and column numbers
- Check file permissions
- Consider using JSON format if you have recurring YAML syntax issues

### Environment variables not working
- Ensure variables are exported
- Check variable names match exactly
- Verify no typos in variable names

### Authentication fails
- Verify credentials are correct
- Check homeserver URL is accessible
- For OIDC, verify client credentials
- **Important:** `user_id` must be set for all authentication types (password, token, OIDC)
  - For token/OIDC: user_id is required to load the encryption store
  - Error message: "user_id is not set in configuration" indicates missing or empty user_id
  - Set via `MATRIX_USER_ID` environment variable or `matrix.user_id` in config.yaml

### Bot doesn't respond to commands in encrypted rooms
- Ensure `user_id` is properly configured (see above)
- Check that the encryption store is loaded successfully
  - Look for "Loaded encryption store" in logs for token/OIDC auth
- Verify the bot has been invited and joined the room
- For encrypted rooms, the bot needs:
  - Valid user_id to load encryption keys
  - Proper encryption setup during login
  - Room keys shared with the bot's device
- If you see "Unable to decrypt message" warnings:
  - The bot may not have received the encryption keys for that room
  - Try reinviting the bot or sending it a message in an unencrypted room first
- If you see "Matrix store and olm account is not loaded" errors:
  - This indicates the encryption store wasn't loaded during login
  - Verify user_id is set correctly
  - Check the bot logged in successfully with encryption support

For more help, see the [Support Guide](support.html).
