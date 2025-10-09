---
layout: default
title: Configuration
nav_order: 4
---

# Configuration Guide

ChatrixCD is configured using JSON files.

## Supported Configuration Format

ChatrixCD uses **HJSON** (Human JSON) for configuration files, which is a superset of JSON that supports:
- **Comments**: Use `//`, `/* */`, or `#` for inline and multi-line comments
- **Trailing commas**: Add trailing commas after the last item in objects and arrays
- **Unquoted keys**: Use keys without quotes for cleaner syntax (optional)
- **Multi-line strings**: Spread strings across multiple lines
- **Full JSON compatibility**: Any valid JSON file is also valid HJSON

Configuration files use the `.json` extension but support all HJSON features. This provides:
- Better documentation through inline comments
- Robust parsing with clear error messages
- Human-friendly syntax with comments and trailing commas
- Wide JSON tooling compatibility

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

1. **Configuration file** (`config.json`) - explicit values in the configuration file take **highest priority**
2. **Default values** (hardcoded) - used when not specified in config file

**Note:** Environment variables are no longer supported. All configuration must be specified in the `config.json` file.

**Example:** If your `config.json` has `user_id` set to `@bot:example.com`:
- `user_id` will be `@bot:example.com` (from the config file)
- If `device_id` is NOT in the config file, it will use the hardcoded default value
- Other unspecified fields (like `device_name`) will use hardcoded defaults

This simplified configuration approach:
- Eliminates confusion about configuration sources
- Makes configuration more explicit and easier to debug
- Centralizes all configuration in a single, documented file

## Configuration File Format

Create a `config.json` file in your working directory. The file supports HJSON format, which allows comments and trailing commas:

```hjson
{
  // Configuration file version - do not modify
  "_config_version": 2,
  
  // Matrix homeserver connection settings
  "matrix": {
    // Matrix homeserver URL (e.g., https://matrix.org)
    "homeserver": "https://matrix.example.com",
    
    // Bot user ID (e.g., @bot:example.com)
    "user_id": "@bot:example.com",
    
    // Authentication type: "password", "token", or "oidc"
    "auth_type": "password",
    
    // Password for password authentication
    "password": "your-secure-password",
    
    // Device name for this bot instance
    "device_name": "ChatrixCD Bot",
    
    // Path to store encryption keys
    "store_path": "./store"  // Trailing comma is OK
  },
  
  // Semaphore UI connection settings
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-semaphore-api-token"
  },
  
  // Bot behavior settings
  "bot": {
    "command_prefix": "!cd",
    "allowed_rooms": []
  }
}
```

**Benefits of HJSON:**
- **Comments**: Document your configuration with inline comments
- **Trailing commas**: No more syntax errors from trailing commas
- **JSON compatible**: Any valid JSON is also valid HJSON
- **Human-friendly**: More readable and maintainable configuration files
- **Clear error messages**: Helpful error messages with line numbers when syntax is invalid

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

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "password": "your-password",
    "auth_type": "password"
  }
}
```

### Token Authentication

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "access_token": "your-access-token",
    "auth_type": "token"
  }
}
```

### OIDC Authentication

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "oidc",
    "oidc_client_id": "your-client-id",
    "oidc_client_secret": "your-client-secret",
    "oidc_issuer": "https://auth.example.com"
  }
}
```

## Access Control

### Allow All Rooms

```json
{
  "bot": {
    "allowed_rooms": []
  }
}
```

### Restrict to Specific Rooms

```json
{
  "bot": {
    "allowed_rooms": [
      "!roomid1:example.com",
      "!roomid2:example.com"
    ]
  }
}
```

## Example Configurations

### Development Setup

```json
{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@mybot:matrix.org",
    "password": "dev-password",
    "device_name": "ChatrixCD Dev",
    "store_path": "./dev-store"
  },
  "semaphore": {
    "url": "http://localhost:3000",
    "api_token": "dev-token"
  },
  "bot": {
    "command_prefix": "!cd",
    "allowed_rooms": []
  }
}
```

### Production Setup with OIDC

```json
{
  "matrix": {
    "homeserver": "https://matrix.company.com",
    "user_id": "@cicd-bot:company.com",
    "auth_type": "oidc",
    "oidc_client_id": "${OIDC_CLIENT_ID}",
    "oidc_client_secret": "${OIDC_CLIENT_SECRET}",
    "oidc_issuer": "https://auth.company.com",
    "device_name": "ChatrixCD Production",
    "store_path": "/var/lib/chatrixcd/store"
  },
  "semaphore": {
    "url": "https://semaphore.company.com",
    "api_token": "${SEMAPHORE_API_TOKEN}"
  },
  "bot": {
    "command_prefix": "!cd",
    "allowed_rooms": [
      "!devops:company.com",
      "!ci-alerts:company.com"
    ],
    "greetings_enabled": true,
    "greeting_rooms": [
      "!devops:company.com"
    ],
    "startup_message": "🚀 CI/CD Bot online!",
    "shutdown_message": "🛑 CI/CD Bot going offline for maintenance"
  }
}
```

### Greeting Messages Configuration

You can configure the bot to send startup and shutdown messages to specific rooms:

```json
{
  "bot": {
    "greetings_enabled": true,
    "greeting_rooms": [
      "!roomid1:example.com",
      "!roomid2:example.com"
    ],
    "startup_message": "🤖 ChatrixCD bot is now online and ready to help with CI/CD tasks!",
    "shutdown_message": "👋 ChatrixCD bot is shutting down. See you later!"
  }
}
```

**Note:** Greeting messages are only sent to rooms explicitly listed in `greeting_rooms`. This allows you to control which rooms receive these notifications, which is especially useful if the bot is in many rooms but you only want status updates in specific ones.

To disable greetings entirely, either:
- Set `greetings_enabled` to `false` in config.json, or
- Leave `greeting_rooms` as an empty array

## Security Best Practices

### Protect Configuration Files

```bash
chmod 600 config.json
chmod 700 store/
```

### Manage Secrets Securely

To protect sensitive information in the config.json file:

- Store config.json in a secure location with restricted file permissions (chmod 600)
- Use secret management systems (like Kubernetes secrets, Vault, etc.) to generate the config file at deployment time
- Keep config.json out of version control (add to .gitignore)
- Use token-based authentication instead of passwords when possible

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
- Check file name is exactly `config.json`
- Verify JSON syntax is valid - parse errors will show exact line and column numbers
  - Common issues: missing commas, trailing commas, unquoted keys, incorrect brackets
  - Use a JSON validator or linter to check syntax
- Check file permissions
- Ensure the file is readable by the bot user

### Authentication fails
- Verify credentials are correct
- Check homeserver URL is accessible
- For OIDC, verify client credentials
- **Important:** `user_id` must be set for all authentication types (password, token, OIDC)
  - For token/OIDC: user_id is required to load the encryption store
  - Error message: "user_id is not set in configuration" indicates missing or empty user_id
  - Set via `matrix.user_id` in config.json

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
