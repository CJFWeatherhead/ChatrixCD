# Semaphore Poll Plugin

This plugin provides task monitoring for Semaphore UI using a polling mechanism. It periodically checks the Semaphore API for task status updates and sends notifications to Matrix rooms.

## Description

The Semaphore Poll plugin is the default task monitoring mechanism for ChatrixCD. It works by:
1. Polling the Semaphore API at regular intervals (default: every 10 seconds)
2. Checking for status changes in monitored tasks
3. Sending notifications to Matrix rooms when tasks complete or fail

This is a reliable approach that works with any Semaphore UI installation without requiring additional configuration or webhook setup.

## Configuration

This plugin is configured through its `plugin.json` file located in the plugin directory.

### plugin.json

```json
{
  "enabled": true,
  "poll_interval": 10,
  "notification_interval": 300
}
```

### Configuration Options

- **`enabled`** (boolean, default: `true`): Enable or disable the plugin
- **`poll_interval`** (integer, default: `10`): Interval in seconds between status checks
- **`notification_interval`** (integer, default: `300`): Interval in seconds for periodic "still running" notifications

### Overriding Configuration

You can override plugin configuration in the main `config.json` file under the `plugins` section (for backwards compatibility):

```json
{
  "bot": {
    "load_plugins": true
  },
  "plugins": {
    "semaphore_poll": {
      "enabled": true,
      "poll_interval": 5,
      "notification_interval": 180
    }
  }
}
```

**Note:** Settings in `config.json` will override those in `plugin.json`.

## Usage

Once loaded, the plugin automatically monitors all tasks started via the `!cd run` command. No additional configuration is needed.

## Advantages

- ✅ Simple setup - works out of the box
- ✅ No additional services required
- ✅ Works with any Semaphore UI version
- ✅ Reliable and battle-tested

## Disadvantages

- ⚠️ Higher API load - polls continuously
- ⚠️ Slight delay in notifications (up to poll_interval seconds)
- ⚠️ More network traffic

## Compatibility

- **Mutually Exclusive With**: `semaphore_webhook` plugin (only one task monitor can be active)
- **Requires**: Semaphore UI API access

## Technical Details

This plugin uses the existing `SemaphoreClient` to poll the `/api/project/{project_id}/tasks/{task_id}` endpoint for status updates.
