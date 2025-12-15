# Integration Testing Setup

This directory contains tools for running integration tests against a live ChatrixCD instance running on a remote machine.

## Features

- **Remote Bot Management**: SSH-based control of ChatrixCD on remote servers
- **Automatic Config Discovery**: Reads and parses bot configuration from remote machines
- **OIDC Authentication Support**: Gracefully handles OIDC-authenticated bots
- **Encrypted Message Reading**: Bots can decrypt and read each other's encrypted messages using shared stores
- **Cross-Bot Verification**: Automatic device verification between multiple bots
- **Enhanced Redaction**: Improved log redaction for Matrix cryptographic data
- **Preauthenticated Testing**: Tests use existing bot sessions without separate test clients
- **Slow Machine Support**: Extended timeouts for remote operations

## Test Types

### Configuration Tests (Always Run)
- `test_bot_config_valid`: Validates bot configuration structure and format

### Interactive Tests (Require Authentication)
- `test_bot_projects_command`: Tests project listing
- `test_bot_responds_to_help`: Tests help command
- `test_bot_responds_to_invalid_command`: Tests error handling
- `test_bot_responds_to_pet_command`: Tests hidden pet command
- `test_bot_responds_to_scold_command`: Tests hidden scold command
- `test_bot_status_command`: Tests status command
- `test_verify_commands`: Tests device verification commands
- `test_sessions_commands`: Tests session management commands
- `test_encrypted_message_reading`: Tests ability to read encrypted messages from verified bots

## OIDC Authentication Handling

When the bot uses OIDC authentication (like Privacy International's setup), the integration tests use the preauthenticated bot sessions from the remote machines. No separate test client authentication is required, as the bots test each other using their existing access tokens and encryption stores.

The tests automatically:

1. **Use existing sessions**: Restore bot sessions using access tokens from remote config/session files
2. **Copy encryption stores**: Transfer remote store directories to enable decryption of encrypted messages
3. **Perform cross-verification**: Bots verify each other to read encrypted responses
4. **Run all tests**: Both configuration and interactive tests execute using authenticated bot sessions

## Device Verification and Encrypted Messages

The integration tests use preauthenticated bot sessions and copy remote encryption stores to enable full testing of encrypted rooms:

1. **Store Transfer**: Encryption keys and session data are copied from remote machines
2. **Cross-Verification Setup**: Bots automatically verify each other using existing trust relationships
3. **Encrypted Message Reading**: Tests can read and validate actual decrypted bot responses
4. **Verification Commands**: Tests include device verification and session management commands
5. **Real Message Validation**: All tests validate actual bot responses instead of "[ENCRYPTED_RESPONSE]"

This enables comprehensive testing of bot-to-bot interactions in encrypted rooms.

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
   # Use explicit Python path to ensure packages install into venv
   uv pip install --python .venv/bin/python -r requirements.txt
   uv pip install --python .venv/bin/python -e .
   uv pip install --python .venv/bin/python pytest pytest-asyncio
   
   # Or use pip directly (after activating venv)
   # pip install -r requirements.txt pytest pytest-asyncio
   # pip install -e .
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
   - `chatrix_dir`: Directory where ChatrixCD is installed
   - `venv_activate`: Command to activate virtual environment
   - `chatrix_command`: Command to start ChatrixCD
   - `matrix`: Matrix configuration (automatically read from remote, but can be overridden)
   - `test_room`: Room ID for testing (automatically read from remote config)
   - `test_timeout`: Timeout for operations
   - `ssh_key_path`: Path to SSH private key

   **Note**: Matrix server details (homeserver, bot user ID, room ID) are automatically read from the remote server's `config.json` file. No separate test client configuration is needed.

### Configuration Options

### Remote Machine Configuration

- `remote_host`: IP/hostname of the remote machine
- `remote_user`: SSH user for initial connection (usually "root")
- `chatrix_user`: User account that runs ChatrixCD
- `chatrix_dir`: Directory where ChatrixCD is installed (usually "~/ChatrixCD")
- `venv_activate`: Command to activate virtual environment
- `chatrix_command`: Command to start ChatrixCD with desired flags

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

## Running the Tests

### Basic Test Run

```bash
python tests/run_integration_tests.py tests/integration_config.json
```

### What Happens During Testing

1. **SSH Connection**: Connects to the remote machine
2. **Config Discovery**: Reads and parses the bot's configuration
3. **Code Update**: Updates ChatrixCD code and dependencies
4. **Bot Startup**: Starts ChatrixCD in the background
5. **Test Execution**: Runs the test suite
6. **Cleanup**: Stops the bot and reports results

### Expected Output

When running integration tests with preauthenticated bot sessions:

```
Reading configuration from remote server...
SSH attempt 1/3: cat /home/chatrix/ChatrixCD/config.json...
Updating ChatrixCD on remote machine...
Starting ChatrixCD on remote machine...
ChatrixCD started with PID: 12345
ChatrixCD is running
Copying encryption stores from remote machines...
Running integration tests...
============================================================ test session starts =============================================================
tests/test_integration_matrix.py::ChatrixCDIntegrationTest::test_bot_config_valid PASSED
tests/test_integration_matrix.py::ChatrixCDIntegrationTest::test_bot_projects_command PASSED
tests/test_integration_matrix.py::ChatrixCDIntegrationTest::test_bot_responds_to_help PASSED
[... other tests PASSED ...]
```

### Test Results

- **PASSED**: All tests pass when bot sessions are properly restored and stores are copied
- **FAILED**: Only if there are actual configuration, connection, or encryption issues

## Security Notes

- Never commit `integration_config.json` with real credentials
- Use SSH keys, not passwords
- Encryption stores are temporarily copied locally for testing but should be handled securely
- The bot should be configured to only respond in authorized rooms

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