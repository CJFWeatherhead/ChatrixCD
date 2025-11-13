# Integration Testing Setup

This directory contains tools for running integration tests against a live ChatrixCD instance running on a remote machine.

## Local Development Setup (macOS with Homebrew)

### Prerequisites

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install uv package manager**:
   ```bash
   brew install uv
   ```

3. **Install Python 3.12+** (if not already installed):
   ```bash
   brew install python@3.14
   ```

### Setup Steps

1. **Clone and enter the repository**:
   ```bash
   git clone https://github.com/CJFWeatherhead/ChatrixCD.git
   cd ChatrixCD
   ```

2. **Create virtual environment**:
   ```bash
   uv venv
   ```

3. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   uv pip install -e .
   uv pip install pytest pytest-asyncio
   ```

5. **Verify installation**:
   ```bash
   python -m pytest tests/test_config.py::TestConfig::test_json_config -v
   ```

### Troubleshooting

- **python-olm build failures**: The integration tests use `matrix-nio` without E2E encryption features to avoid build issues with `python-olm` on macOS.
- **CMake errors**: Ensure you have `cmake` installed: `brew install cmake`
- **Permission issues**: Make sure your SSH keys have correct permissions: `chmod 600 ~/.ssh/id_rsa`

## Remote Machine Setup

1. **Copy the configuration template:**
   ```bash
   cp tests/integration_config.json.example tests/integration_config.json
   ```

2. **Edit the configuration:**
   Update `tests/integration_config.json` with your specific settings:
   - `remote_host`: IP address of the machine running ChatrixCD
   - `remote_user`: SSH user for initial connection (usually "root")
   - `chatrix_user`: User account that runs ChatrixCD
   - `test_client`: Credentials for the test Matrix user (user_id, password)
   - `ssh_key_path`: Path to your SSH private key

   **Note**: Matrix server details (homeserver, bot user ID, room ID) are automatically read from the remote server's `config.json` file.

### Configuration Options

### Remote Machine Configuration

- `remote_host`: IP/hostname of the remote machine
- `remote_user`: SSH user for initial connection (usually "root")
- `chatrix_user`: User account that runs ChatrixCD
- `chatrix_dir`: Directory where ChatrixCD is installed (usually "~/ChatrixCD")
- `venv_activate`: Command to activate virtual environment
- `chatrix_command`: Command to start ChatrixCD with desired flags

### Test Client Configuration

- `user_id`: Matrix user ID for the test client
- `password`: Password for the test client

### Test Configuration

- `test_timeout`: Timeout for test runs (seconds)
- `ssh_key_path`: Path to SSH private key

## Running Integration Tests

### Automated (Recommended)

Use the provided script to automatically start/stop the remote bot:

```bash
python tests/run_integration_tests.py tests/integration_config.json
```

This will:
1. SSH to the remote machine
2. Read Matrix configuration from the remote `config.json`
3. Update code and dependencies on remote machine
4. Start ChatrixCD in the background
5. Run the integration tests
6. Stop ChatrixCD
7. Report results

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