# Integration Testing Setup

This directory contains tools for running integration tests against a live ChatrixCD instance running on a remote machine.

## Setup

1. **Copy the configuration template:**
   ```bash
   cp tests/integration_config.json.example tests/integration_config.json
   ```

2. **Edit the configuration:**
   Update `tests/integration_config.json` with your specific settings:
   - `remote_host`: IP address of the machine running ChatrixCD
   - `remote_user`: SSH user (usually "root")
   - `chatrix_user`: User account running ChatrixCD
   - `matrix`: Matrix server and credentials for the test client
   - `ssh_key_path`: Path to your SSH private key

3. **Ensure SSH access:**
   Make sure you can SSH to the remote machine without a password:
   ```bash
   ssh -i ~/.ssh/id_rsa root@100.96.234.70
   ```

4. **Install dependencies:**
   The tests require `matrix-nio` which should already be installed.

## Running Integration Tests

### Automated (Recommended)

Use the provided script to automatically start/stop the remote bot:

```bash
python tests/run_integration_tests.py tests/integration_config.json
```

This will:
1. SSH to the remote machine
2. Start ChatrixCD in the background
3. Run the integration tests
4. Stop ChatrixCD
5. Report results

### Manual Testing

If you want to start/stop the bot manually:

1. **Start the bot remotely:**
   ```bash
   ssh root@100.96.234.70
   su chatrix
   cd ~/ChatrixCD
   source .venv/bin/activate
   chatrix -NLCvv &
   ```

2. **Run tests locally:**
   ```bash
   INTEGRATION_CONFIG=tests/integration_config.json python -m pytest tests/test_integration_matrix.py -v
   ```

3. **Stop the bot remotely:**
   ```bash
   # Find the process
   ps aux | grep chatrix
   # Kill it
   kill <PID>
   ```

## Configuration Options

### Remote Machine Configuration

- `remote_host`: IP/hostname of the remote machine
- `remote_user`: SSH user for initial connection (usually "root")
- `chatrix_user`: User account that runs ChatrixCD
- `chatrix_dir`: Directory where ChatrixCD is installed (usually "~/ChatrixCD")
- `venv_activate`: Command to activate virtual environment
- `chatrix_command`: Command to start ChatrixCD with desired flags

### Matrix Configuration

- `homeserver`: Matrix homeserver URL
- `user_id`: Test user ID for sending messages
- `password`: Test user password
- `room_id`: Room ID where ChatrixCD is active
- `bot_user_id`: ChatrixCD bot's user ID

### Test Configuration

- `test_timeout`: Timeout for test runs (seconds)
- `ssh_key_path`: Path to SSH private key

## Test Coverage

The integration tests cover:

- Basic bot responsiveness (`!cd help`)
- Error handling for invalid commands
- Hidden commands (`!cd pet`, `!cd scold`)
- Status commands
- Projects listing

## Security Notes

- Never commit `integration_config.json` with real credentials
- Use SSH keys, not passwords
- Ensure the test user has minimal permissions
- The bot should be configured to only respond in the test room

## Troubleshooting

### SSH Connection Issues

- Verify SSH key is correct: `ssh -i ~/.ssh/id_rsa root@remote_host`
- Check that the remote machine is accessible from your network

### Bot Won't Start

- Check that the virtual environment exists on the remote machine
- Verify ChatrixCD is properly installed
- Check logs: `tail -f ~/ChatrixCD/chatrix.log`

### Tests Fail

- Ensure the Matrix credentials are correct
- Verify the bot is joined to the test room
- Check that the room ID is correct
- Look at Matrix server logs if available

### Matrix Connection Issues

- Test Matrix login manually with a Matrix client
- Verify homeserver URL is correct
- Check that the test user can join the room