# Semaphore Webhook Plugin

This plugin provides task monitoring for Semaphore UI using webhook notifications via Gotify. It receives push notifications when task status changes, providing instant notifications without polling.

## Description

The Semaphore Webhook plugin provides a more efficient alternative to polling. It works by:

1. Configuring Semaphore UI to send notifications to Gotify when task status changes
2. Listening for Gotify notifications via WebSocket or webhook
3. Immediately sending notifications to Matrix rooms when events are received

This approach is more efficient and provides instant notifications.

## Prerequisites

- Gotify server (for receiving Semaphore notifications)
- Semaphore UI configured to send notifications to Gotify

## Configuration

### 1. Set up Gotify

Install and configure a Gotify server to receive Semaphore notifications.

### 2. Configure Semaphore UI

Configure Semaphore UI to send notifications to your Gotify server:

1. Go to Semaphore UI → Project Settings → Integrations
2. Add a new "Gotify" integration
3. Enter your Gotify server URL and application token
4. Enable notifications for task events (started, completed, failed)

### 3. Configure ChatrixCD

This plugin is configured through its `plugin.json` file located in the plugin directory.

#### plugin.json

```json
{
  "enabled": false,
  "gotify_url": "https://gotify.example.com",
  "gotify_token": "your_gotify_client_token",
  "gotify_app_token": "your_gotify_app_token",
  "webhook_mode": "websocket",
  "fallback_poll_interval": 60,
  "ignore_ssl": false
}
```

### Configuration Options

- **`enabled`** (boolean, default: `false`): Enable or disable the plugin
- **`gotify_url`** (string, required): Gotify server URL
- **`gotify_token`** (string, required): Gotify client token for authentication
- **`gotify_app_token`** (string, required): Gotify application token
- **`webhook_mode`** (string, default: `"websocket"`): Connection mode (`"websocket"` or `"polling"`)
- **`fallback_poll_interval`** (integer, default: `60`): Fallback polling interval if webhook connection fails
- **`ignore_ssl`** (boolean, default: `false`): Ignore SSL certificate verification (useful for self-signed certificates)

### Overriding Configuration

You can override plugin configuration in the main `config.json` file (for backwards compatibility):

```json
{
  "bot": {
    "load_plugins": true
  },
  "plugins": {
    "semaphore_webhook": {
      "enabled": true,
      "gotify_url": "https://your-gotify.com",
      "gotify_token": "your_token",
      "gotify_app_token": "your_app_token"
    }
  }
}
```

**Note:** Settings in `config.json` will override those in `plugin.json`.

## Usage

Once configured, the plugin automatically monitors all tasks started via the `!cd run` command by listening for Gotify notifications.

## Advantages

- ✅ Instant notifications - no polling delay
- ✅ Lower API load - only checks on events
- ✅ More efficient - less network traffic
- ✅ Scalable - handles many concurrent tasks easily

## Disadvantages

- ⚠️ Requires Gotify server setup
- ⚠️ Additional complexity in configuration
- ⚠️ Requires Semaphore UI notification configuration
- ⚠️ May miss events if webhook connection is lost (falls back to polling)

## Compatibility

- **Mutually Exclusive With**: `semaphore_poll` plugin (only one task monitor can be active)
- **Requires**:
  - Gotify server
  - Semaphore UI with Gotify integration configured

## Technical Details

This plugin connects to Gotify via WebSocket to receive real-time notifications about Semaphore task status changes. It maintains a mapping of task IDs to Matrix rooms for notification routing.

## Troubleshooting

### No notifications received

1. Check Gotify server is accessible from ChatrixCD
2. Verify Gotify token is correct
3. Ensure Semaphore UI notification integration is properly configured
4. Check Semaphore UI is sending notifications (test in Gotify UI)

### Connection issues

The plugin will automatically fall back to periodic polling if the WebSocket connection fails. Check logs for connection errors.
