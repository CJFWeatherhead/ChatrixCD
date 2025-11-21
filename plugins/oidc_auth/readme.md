# OIDC Authentication Plugin

Provides OIDC (OpenID Connect) / SSO authentication support for ChatrixCD.

## Overview

This plugin enables OIDC authentication as an alternative to password-based authentication. When enabled and the bot is configured with `auth_type: "oidc"`, the bot will use SSO/OIDC login flow instead of direct password authentication.

## Features

- **OIDC/SSO Login**: Authenticate using external identity providers (Google, GitHub, Keycloak, etc.)
- **Multiple Providers**: Supports homeservers with multiple identity provider options
- **Interactive TUI**: Beautiful modal screen for token input when using interactive mode
- **Console Fallback**: Works in non-interactive mode with console prompts
- **Session Persistence**: Saves and restores OIDC sessions automatically
- **Provider Detection**: Automatically detects and displays available identity providers

## Configuration

### Enable OIDC Plugin

The plugin is enabled by default. To disable it, add to your `config.json`:

```json
{
  "plugins": {
    "oidc_auth": {
      "enabled": false
    }
  }
}
```

### Configure Bot for OIDC

Set your Matrix authentication to use OIDC:

```json
{
  "matrix": {
    "homeserver": "https://matrix.example.com",
    "user_id": "@bot:example.com",
    "auth_type": "oidc",
    "oidc_redirect_url": "http://localhost:8080/callback"
  }
}
```

**Note**: The `oidc_redirect_url` is where your browser will be redirected after authentication. It does NOT need to be a running web server - you'll copy the token from the URL. Common values:

- `http://localhost:8080/callback` (default, for local use)
- `urn:ietf:wg:oauth:2.0:oob` (OAuth2 out-of-band for CLI apps)
- `https://your-domain.com/auth/callback` (if you have a web handler)

## How It Works

### Authentication Flow

1. **Bot starts** with `auth_type: "oidc"`
2. **Plugin checks** for saved session
   - If valid session exists → restores it automatically
   - If no session or expired → proceeds to interactive login
3. **Interactive login**:
   - Plugin queries homeserver for available identity providers
   - Builds SSO redirect URL
   - Shows TUI modal (interactive mode) or console prompt (log-only mode)
   - User visits URL, logs in via SSO provider
   - User copies `loginToken` from redirect URL
   - User pastes token into TUI/console
4. **Plugin completes login** with token
5. **Session saved** for future use

### TUI Integration

When running in interactive mode (`chatrixcd`), the plugin provides a modal screen for token input:

```
┌─────────────────────────────────────────────────┐
│          🔐 OIDC Authentication Required        │
│                                                 │
│  Please complete these steps to authenticate:  │
│                                                 │
│  1. Open this URL in your browser:             │
│  https://matrix.example.com/_matrix/client/... │
│                                                 │
│  2. Log in with your credentials               │
│                                                 │
│  3. After login, you'll be redirected to:      │
│     http://localhost:8080/callback?loginToken=...│
│                                                 │
│  4. Copy the 'loginToken' value and paste below│
│                                                 │
│  Login Token:                                  │
│  [________________________________]             │
│                                                 │
│          [Submit]      [Cancel]                │
└─────────────────────────────────────────────────┘
```

### Console Mode

In log-only mode (`chatrixcd -L`), instructions are printed to console and token is read from stdin.

## Architecture

### Plugin Components

- **plugin.py**: Main plugin logic, authentication flow
- **oidc_tui.py**: TUI modal screen for token input
- **meta.json**: Plugin metadata
- **plugin.json**: Default configuration

### Integration with Bot

The plugin:
1. Registers itself as `bot.oidc_plugin` during initialization
2. Bot checks for OIDC plugin when `auth_type == "oidc"`
3. Bot calls `plugin.login_oidc(bot)` to perform authentication
4. Plugin uses bot's Matrix client to complete the login

### Code Flow

```
bot.login()
  ├─ if auth_type == "password": 
  │    └─ Direct password login (core)
  │
  └─ if auth_type == "oidc":
       ├─ Check for bot.oidc_plugin
       ├─ Try session restoration
       └─ If needed: plugin.login_oidc(bot)
            ├─ Get identity providers
            ├─ Build redirect URL
            ├─ Call token_callback (TUI or console)
            ├─ User authenticates
            └─ Complete login with token
```

## Advantages of Plugin Architecture

### 🎯 **Separation of Concerns**
- Core bot handles password auth (simple, always works)
- Plugin handles OIDC (optional, complex)
- Easy to maintain, test, and debug separately

### 🔌 **Optional Dependency**
- Users who don't need OIDC can disable the plugin
- Reduces complexity for simple deployments
- No OIDC code loaded if disabled

### 🧪 **Better Testing**
- Core auth logic simpler to test
- OIDC logic isolated and testable independently
- Mock plugin for testing core without OIDC

### 📦 **Modular Codebase**
- ~300 lines of OIDC code moved from core to plugin
- Core bot.py cleaner and more focused
- Plugin self-contained with TUI integration

### 🚀 **Easy to Extend**
- Add more auth methods as plugins (SAML, LDAP, etc.)
- Customize OIDC flow without touching core
- Replace with different OIDC implementation if needed

## Troubleshooting

### Plugin Not Loading

Check logs for:
```
INFO: OIDC Authentication plugin initialized
INFO: OIDC Authentication plugin started
```

If missing, verify:
- Plugin is enabled in config
- No syntax errors in plugin files
- Plugin dependencies satisfied

### OIDC Login Fails

Common issues:

1. **Server doesn't support SSO**:
   ```
   ERROR: Server does not support SSO/OIDC login
   ```
   → Check homeserver supports OIDC (Matrix Synapse, Dendrite, etc.)

2. **Invalid token**:
   ```
   ERROR: The login token is invalid or has expired
   ```
   → Token used incorrectly, expired, or already used. Try again.

3. **Token callback fails**:
   ```
   ERROR: Token callback failed
   ```
   → TUI issue. Try log-only mode: `chatrixcd -L`

### TUI Screen Not Appearing

If OIDC screen doesn't show in interactive mode:
- Check TUI is running (not `-L` flag)
- Verify `oidc_tui.py` exists and has no syntax errors
- Check logs for TUI registration messages

### Disabling Plugin

To revert to password auth:

1. Change config: `"auth_type": "password"`
2. Add password: `"password": "your_password"`
3. Optionally disable plugin:
   ```json
   "plugins": {
     "oidc_auth": {
       "enabled": false
     }
   }
   ```

## Development

### Testing

Test the plugin:
```bash
# With real homeserver (integration test)
chatrixcd -vv  # verbose logging

# Unit tests (TODO)
python -m unittest tests.test_oidc_plugin
```

### Extending

To add custom OIDC behavior:

1. Fork `plugins/oidc_auth/plugin.py`
2. Override methods like `_get_token_from_user()`
3. Register custom TUI screens
4. Update `meta.json` with new name/version

### API

The plugin provides:

```python
# Set custom token callback
plugin.set_token_callback(async_callback_function)

# Perform OIDC login
success = await plugin.login_oidc(bot)

# Get identity providers
providers = await plugin._get_identity_providers(bot)
```

## See Also

- [Matrix OIDC Specification](https://spec.matrix.org/v1.8/client-server-api/#sso-login)
- [ChatrixCD Plugin Development](../../docs/PLUGIN_DEVELOPMENT.md)
- [TUI Architecture](../../docs/TUI_ARCHITECTURE.md)
- [Configuration Guide](../../docs/configuration.md)

## License

GPL-3.0 - Same as ChatrixCD
