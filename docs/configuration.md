---
layout: default
title: Configuration
nav_order: 4
---

# ⚙️ Configuration Guide

> **Configure ChatrixCD to fit your workflow** - JSON-based configuration with human-friendly HJSON support!

---

## 📝 Configuration Format

<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0;">
  <strong>💡 Pro Tip:</strong> ChatrixCD uses <strong>HJSON</strong> (Human JSON) - write cleaner configs with comments and trailing commas!
</div>

### ✨ HJSON Features

| Feature | Description | Example |
|---------|-------------|---------|
| 💬 Comments | Use `//`, `/* */`, or `#` | `// This is a comment` |
| 📍 Trailing Commas | No more syntax errors! | `{ "key": "value", }` |
| 🔤 Unquoted Keys | Cleaner syntax | `{ key: "value" }` |
| 📄 Multi-line Strings | Spread text across lines | See docs |
| ✅ JSON Compatible | All JSON files work | Standard `.json` files |

<details>
<summary><strong>📖 Show Example HJSON Config</strong></summary>

```json
{
  // Matrix server configuration
  matrix: {
    homeserver: "https://matrix.example.com",
    user_id: "@bot:example.com",
    // Use password or OIDC authentication
    auth_type: "password",
    password: "your-secure-password",
  },
  
  // Semaphore UI connection
  semaphore: {
    url: "https://semaphore.example.com",
    api_token: "your-api-token",
  },
  
  // Bot behavior settings
  bot: {
    command_prefix: "!cd",
    allowed_rooms: [],  // Empty = all rooms
    log_file: "bot.log",
  }
}
```
</details>

---

## 🔄 Configuration Versioning

<div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 1rem; margin: 1rem 0;">
  <strong>✅ Automatic Migration:</strong> Your config auto-upgrades when you update ChatrixCD!
</div>

### Current Version: **3**

| Step | What Happens |
|------|-------------|
| 🔍 **Detect** | ChatrixCD detects older config version |
| 💾 **Backup** | Creates `.backup` file automatically |
| ⬆️ **Migrate** | Upgrades to current version |
| ✅ **Save** | Saves migrated config |

### 📋 Version History

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 1rem 0;">
  <div style="border: 2px solid #e5e7eb; border-radius: 8px; padding: 1rem;">
    <strong>📦 Version 1</strong>
    <p style="margin: 0.5rem 0; color: #6b7280;">Original format</p>
  </div>
  <div style="border: 2px solid #e5e7eb; border-radius: 8px; padding: 1rem;">
    <strong>💬 Version 2</strong>
    <p style="margin: 0.5rem 0; color: #6b7280;">Added greetings support</p>
  </div>
  <div style="border: 2px solid #3b82f6; border-radius: 8px; padding: 1rem; background: #eff6ff;">
    <strong>🔐 Version 3 (Current)</strong>
    <p style="margin: 0.5rem 0; color: #1e40af;">SSL/TLS + log file config</p>
  </div>
</div>

---

## 🎯 Configuration Priority

<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0;">
  <strong>⚠️ Important:</strong> Environment variables are <strong>not supported</strong>. Use <code>config.json</code> only!
</div>

### Priority Order (Highest → Lowest)

1. **🏆 Configuration File** (`config.json`) - Your settings always win
2. **📚 Default Values** (hardcoded) - Used when not specified

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
  "_config_version": 3,
  
  // Matrix homeserver connection settings
  "matrix": {
    // Matrix homeserver URL (e.g., https://matrix.org)
    "homeserver": "https://matrix.example.com",
    
    // Bot user ID (e.g., @bot:example.com)
    "user_id": "@bot:example.com",
    
    // Authentication type: "password" or "oidc"
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

## Authentication Methods

ChatrixCD supports two authentication methods for Matrix servers:

### Password Authentication

Traditional username/password authentication:

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

### OIDC Authentication

ChatrixCD uses Matrix's native SSO/OIDC flow. The Matrix server handles the OIDC provider configuration.

**Minimal configuration (recommended):**
```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "oidc"
  }
}
```

**With custom redirect URL:**
```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "oidc",
    "oidc_redirect_url": "https://your-domain.com/auth/callback"
  }
}
```

**Authentication flow:**
1. Bot displays SSO authentication URL
2. Open URL in browser and authenticate with your OIDC provider
3. Browser redirects to `oidc_redirect_url` with `loginToken` parameter
4. Copy the callback URL (or just the token) and paste into bot
5. Bot completes login automatically

## SSL/TLS Configuration for Semaphore

ChatrixCD provides flexible SSL/TLS configuration options for connecting to Semaphore UI, which is especially useful when Semaphore is running with self-signed certificates or custom certificate authorities.

### Default Behavior (SSL Verification Enabled)

By default, SSL certificate verification is enabled:

```json
{
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token"
  }
}
```

### Disable SSL Verification (Self-Signed Certificates)

**⚠️ Warning:** Only disable SSL verification in trusted development or internal environments.

```json
{
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token",
    "ssl_verify": false
  }
}
```

### Custom CA Certificate

If Semaphore uses a certificate signed by a custom Certificate Authority:

```json
{
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token",
    "ssl_ca_cert": "/path/to/custom-ca.crt"
  }
}
```

### Client Certificate Authentication

For mutual TLS (mTLS) authentication where the client must present a certificate:

```json
{
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token",
    "ssl_client_cert": "/path/to/client.crt",
    "ssl_client_key": "/path/to/client.key"
  }
}
```

### Combined Configuration

You can combine custom CA certificate with client certificate authentication:

```json
{
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token",
    "ssl_ca_cert": "/path/to/custom-ca.crt",
    "ssl_client_cert": "/path/to/client.crt",
    "ssl_client_key": "/path/to/client.key"
  }
}
```

**Note:** If the client certificate key is in the same file as the certificate, you can omit `ssl_client_key`.

### SSL Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ssl_verify` | boolean | `true` | Enable/disable SSL certificate verification |
| `ssl_ca_cert` | string | `""` | Path to custom CA certificate bundle file |
| `ssl_client_cert` | string | `""` | Path to client certificate file for mTLS |
| `ssl_client_key` | string | `""` | Path to client certificate private key file |

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
    "oidc_redirect_url": "https://company.com/auth/callback",
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

**Note:** The Matrix SSO/OIDC flow handles authentication through the Matrix server. You don't need to provide OIDC client credentials directly - the Matrix server manages the OIDC provider integration.

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

### Log File Configuration

You can configure the path to the log file:

```json
{
  "bot": {
    "log_file": "chatrixcd.log"
  }
}
```

**Default:** `chatrixcd.log` (in the current working directory)

**Examples:**
- Absolute path: `"/var/log/chatrixcd/bot.log"`
- Relative path: `"logs/chatrixcd.log"`
- Custom name: `"my-bot.log"`

The log file location is used both for logging output and for the TUI log viewer. Make sure the bot has write permissions to the specified path.

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
- Use OIDC authentication for better security when available

### Rotate Credentials Regularly

- Change bot password periodically
- Regenerate API tokens regularly

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
- For OIDC, follow the SSO authentication flow
- **Important:** `user_id` must be set for all authentication types (password, OIDC)
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
