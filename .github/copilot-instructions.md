# GitHub Copilot Instructions for ChatrixCD

This file provides repository-specific guidance for GitHub Copilot when working with the ChatrixCD project.

## Project Overview

ChatrixCD is a Matrix bot that integrates with Semaphore UI to enable CI/CD automation through chat. The bot supports:

- End-to-end encrypted Matrix rooms using matrix-nio SDK
- Native Matrix authentication (password and OIDC/SSO)
- Interactive Text User Interface (TUI) for bot management
- Asynchronous Python architecture
- Real-time task monitoring and status updates
- Reaction-based confirmations for quick interactions
- Sassy and fun personality with emoji and engaging responses (but is never rude)

## Architecture

### Core Components

- **main.py**: Application entry point and lifecycle management
- **config.py**: Configuration management (JSON with HJSON support)
- **auth.py**: Matrix authentication configuration validator
- **bot.py**: Matrix client integration and event handling
- **commands.py**: Command parser and task orchestration
- **semaphore.py**: Semaphore UI REST API client
- **tui.py**: Text User Interface (interactive mode)
- **redactor.py**: Sensitive information redaction
- **aliases.py**: Alias management for Matrix rooms
- **file_watcher.py**: Configuration file watcher and reloader
- **config_wizard.py**: Initial configuration setup wizard

### Key Technologies

- **matrix-nio**: Matrix protocol client with E2E encryption and native auth (primary SDK)
  - Handles all Matrix protocol communication
  - Provides E2E encryption with Olm/Megolm
  - Supports password and OIDC/SSO authentication
  - Device verification (emoji, QR code, fingerprint)
- **aiohttp**: Async HTTP client for Semaphore API
- **Textual**: Terminal UI framework for interactive TUI
- **hjson**: Human-friendly JSON parser for configuration files

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Maximum line length: 100 characters (flexible for readability)
- Use type hints for function parameters and return values
- Add docstrings to all public functions, classes, and modules (Google or NumPy style)
- Keep functions focused and single-purpose

### Code Example

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    # Implementation
    return True
```

### Async/Await Usage

- Use async/await throughout the codebase
- Properly handle async context managers
- Use `aiohttp.ClientSession` for HTTP requests
- Ensure proper cleanup with try/finally or async context managers

### Error Handling

- Use try/except blocks for expected errors
- Log errors with appropriate severity levels
- Provide user-friendly error messages in chat responses
- Never expose sensitive information in error messages

### Bot Personality

ChatrixCD has a distinctive, engaging personality:

- **Sassy but Friendly**: Responses should be witty and unpredictable, but never rude
- **Emoji-Rich**: Use emoji liberally to make responses fun and visually appealing 🎉
- **Personal Touch**: Address users by name when responding (e.g., "username 👋")
- **Variety**: Randomize response messages to avoid repetition and maintain engagement
- **Reaction Support**: Users can confirm actions with emoji reactions (👍/👎) instead of messages
- **Rich Formatting**: Use HTML formatting for bold, italics, and links in messages. Use data-mx-color and data-mx-bg-color attributes for custom colors.
- **Maintain Compliance with Matrix 1.10+**: Ensure all messages and features comply with Matrix protocol standards.

#### Easter Eggs

The bot includes hidden commands for fun interactions:

- `!cd pet` - Positive reinforcement, the bot responds with appreciation
- `!cd scold` - Negative feedback, the bot responds with apologetic messages

These commands are **undocumented** and should remain as delightful discoveries for users.

## Configuration

### Configuration

Configuration is loaded exclusively from JSON files with HJSON support (JSON with comments):

1. JSON configuration file (`config.json`)
2. Default values

### Accessing Configuration

```python
from chatrixcd.config import Config

config = Config()
matrix_config = config.get_matrix_config()
```

### Configuration Format

- Use JSON or HJSON format (HJSON allows comments and trailing commas)
- Supports automatic migration between config versions
- Schema validation with clear error messages

## Testing

### Test Structure

- Tests are in the `tests/` directory
- Name test files `test_<module_name>.py`
- Use descriptive test method names: `test_<what>_<condition>_<expected>`
- Use unittest framework (standard library)

### Test Example

```python
import unittest
from chatrixcd.config import Config

class TestConfig(unittest.TestCase):
    def test_load_config_from_json(self):
        """Test configuration loading from JSON file."""
        # Test implementation
        pass
```

### Running Tests

```bash
# Ensure virtual environment is activated
uv venv  # Create if not exists
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest tests.test_config

# Run integration tests (requires remote setup)
python tests/run_integration_tests.py tests/integration_config.json
```

### Integration Testing Debugging Guide

When integration tests fail, follow this systematic debugging approach:

#### 1. Common Issues and Solutions

**Python Cache Issues:**

- **Symptom**: Old code running despite git pull
- **Cause**: Python bytecode cache (`__pycache__`, `.pyc` files) not cleared
- **Solution**: The test runner now automatically clears cache before starting bots
- **Manual Fix**: SSH to remote and run:
  ```bash
  cd /home/chatrix/ChatrixCD
  find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
  find . -name "*.pyc" -delete 2>/dev/null
  ```

**Git Sync Issues:**

- **Symptom**: Remote machine has old commits despite `git pull`
- **Cause**: Git thinking it's up-to-date when origin has moved forward
- **Solution**: Test runner now uses `git fetch -f origin main && git reset --hard origin/main`
- **Manual Fix**: SSH to remote and run:
  ```bash
  cd /home/chatrix/ChatrixCD
  git fetch -f origin main
  git reset --hard origin/main
  git log -1 --oneline  # Verify correct commit
  ```

**Dependency Installation Issues:**

- **Symptom**: Import errors or missing packages on remote
- **Cause**: Using wrong pip/uv or not targeting virtualenv
- **Solution**: Test runner uses `uv pip install --python .venv/bin/python`
- **Note**: This is CRITICAL - using just `uv pip install` may not install into venv
- **Verification**: Check remote has vodozemac (should have prebuilt wheels):
  ```bash
  ssh root@<remote> "su - chatrix -c '.venv/bin/python -c \"import vodozemac; print(vodozemac.__version__)\"'"
  ```

#### 2. Debugging Workflow

**Step 1: Check if bots are actually running**

```bash
ssh root@<remote_host> "ps aux | grep chatrix | grep -v grep"
```

**Step 2: Check bot logs for errors**

```bash
ssh root@<remote_host> "cat /home/chatrix/ChatrixCD/chatrix.log | sed 's/\x1b\[[0-9;]*m//g' | tail -100 | grep -E '(ERROR|Traceback)'"
```

**Step 3: Verify code version on remote**

```bash
ssh root@<remote_host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && git log -1 --oneline'"
```

**Step 4: Check specific file for known bugs**

```bash
# Example: checking for the displayname bug
ssh root@<remote_host> "grep -n 'displayname\|display_name' /home/chatrix/ChatrixCD/chatrixcd/commands.py | head -5"
```

**Step 5: Test bot manually**

```bash
# Stop old bot and start fresh
ssh root@<remote_host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && killall -9 chatrixcd; .venv/bin/chatrixcd -vv -L' &"
# Send test message to bot in Matrix room
# Check if bot responds
```

#### 3. Integration Test Architecture

The integration test runner (`tests/run_integration_tests.py`) performs these steps:

1. **Cleanup**: Clear Python cache, stop old processes
2. **Update**: Force fetch from origin, reset to latest commit
3. **Dependencies**: Install using `uv pip install --python .venv/bin/python`
4. **Start**: Launch bot in background with nohup
5. **Copy Stores**: Copy encryption stores from remote to local
6. **Test**: Run pytest against live bots
7. **Collect Logs**: Gather logs from remote machines
8. **Cleanup**: Stop bots, cleanup temp directories

**Key Points:**

- Uses SSH with Tailscale IPv6 addresses
- Bots must already be configured on remote machines
- Test client authenticates locally with stores copied from remote
- **NO test_client section needed** in integration_config.json - uses bot stores

#### 4. When Tests Timeout

**Symptoms:**

- Tests report "Command timed out after 20 seconds"
- Bot not responding to commands

**Possible Causes:**

1. Bot crashed during startup (check logs for ERROR)
2. Bot ignoring old messages (check "Ignoring old message" in logs)
3. Bot not in the test room
4. Semaphore API unreachable from bot
5. Encryption issues preventing message decryption

**Debug Steps:**

1. Check if bot PID still exists: `ps | grep <pid>`
2. Check bot logs for latest activity
3. Manually send message to bot in Matrix
4. Verify bot has proper permissions in room
5. Check if encryption is working (look for "Encryption not enabled" warnings)

#### 5. Quick Reference Commands

```bash
# Check bot is running
ssh root@<host> "ps aux | grep chatrix"

# View last 50 lines of bot log (with colors stripped)
ssh root@<host> "cat /home/chatrix/ChatrixCD/chatrix.log | sed 's/\x1b\[[0-9;]*m//g' | tail -50"

# Check git status on remote
ssh root@<host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && git status'"

# Force update remote to latest
ssh root@<host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && git fetch -f origin main && git reset --hard origin/main'"

# Clear cache and restart bot
ssh root@<host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && find . -name __pycache__ -type d -exec rm -rf {} + ; killall chatrixcd; nohup .venv/bin/chatrixcd -L > chatrix.log 2>&1 &'"

# Check if vodozemac is installed
ssh root@<host> "su - chatrix -c 'cd /home/chatrix/ChatrixCD && .venv/bin/python -c \"import vodozemac; print(vodozemac)\""
```

### Testing Guidelines

Testing is crucial for ChatrixCD to ensure reliability and maintainability. Follow these guidelines when writing tests:

- Mock external services (Matrix server, Semaphore API)
- Test edge cases: empty inputs, None values, errors
- Keep tests isolated and independent
- Write tests for new functionality
- Use textual.pilot for TUI component testing
- Use coverage tools to ensure unit test code coverage
  - Aim for at least 90% code coverage
- Integrate tests into CI pipeline
- Run tests on every pull request
- Ensure all tests pass before merging
- **IMPORTANT**: Tests should be meaningful, not just for coverage metrics, and should validate actual functionality.
- Wherever possible attempt end-to-end tests that cover real-world scenarios.
  - Use public information to build realistic test cases.
- **Integration Testing**: Do not add or reintroduce a `test_client` section in `integration_config.json`. Integration tests use preauthenticated bot sessions from remote machines to test each other. No separate test client authentication is needed.

## Text User Interface (TUI)

### TUI Overview

ChatrixCD includes an interactive Text User Interface (TUI) for bot management:

- **Status Monitoring**: View bot status, connections, and metrics
- **Room Management**: View and manage joined Matrix rooms
- **Session Management**: Manage Olm encryption sessions
- **Device Verification**: Emoji and QR code verification for E2E encryption
- **Configuration Editing**: Interactive configuration editing
- **Log Viewing**: Real-time log viewing
- **Message Sending**: Send messages to rooms directly
- **Alias Management**: Allow alias creation and management

### TUI Implementation

- Built with Textual framework
- Located in `chatrixcd/tui.py`
- Launches by default when running interactively
- Can be disabled with `-L` (log-only mode) flag
- Supports mouse and keyboard navigation

## Commands

### Command Structure

- All commands start with `!cd` (configurable prefix)
- Format: `!cd <command> [arguments]`
- Commands should provide clear feedback to users
- Handle errors gracefully with user-friendly messages

### Available Commands

- `help`: Show help message
- `projects`: List Semaphore projects
- `templates <project_id>`: List templates
- `run <project_id> <template_id>`: Start task
- `status <task_id>`: Check task status
- `stop <task_id>`: Stop task
- `logs <task_id>`: Get task logs

## Security Considerations

### Credentials

- Never log credentials, tokens, or passwords
- Store configuration files securely with proper file permissions
- Store encryption keys securely in the `store/` directory
- Never commit `config.json` with real credentials

### Access Control

- Respect `allowed_rooms` configuration
- Check room permissions before responding to commands
- Validate user permissions for admin commands

### API Security

- Use HTTPS for all external endpoints
- Validate API responses before processing
- Implement proper timeout handling
- Use minimal required API permissions

## Dependencies

### Adding Dependencies

- Add to `requirements.txt`
- Keep dependencies minimal
- Prefer standard library when possible
- Document why new dependencies are needed

### Dependency Versions

- Specify minimum versions in `requirements.txt`
- Test compatibility with specified versions
- Consider security implications of dependencies

## Documentation

### Types of Documentation

When adding features, update relevant documentation:

- **README.md**: Overview, features, basic usage
- **INSTALL.md**: Installation and configuration
- **QUICKSTART.md**: Getting started guide
- **ARCHITECTURE.md**: Technical architecture (in docs/)
- **CONTRIBUTING.md**: Development guidelines
- **CHANGELOG.md**: Record of changes
- **dev/ai/docs/**: AI/LLM generated context documentation, audits, and development notes

### AI/LLM Generated Documentation

Context documentation, audit trails, and non-critical project documentation should be placed in `dev/ai/docs/`:

- **Implementation Plans**: Detailed plans for features or migrations
- **Audit Trails**: Records of significant changes, fixes, or integrations
- **Evaluation Documents**: Test results, compliance checks, assessments
- **Migration Notes**: Notes from version migrations or refactoring
- **Context Documents**: Supporting documentation that provides background

**Naming Convention**: Use underscores and block capitals (e.g., `ENCRYPTION_FIXES_SUMMARY.md`)

**What NOT to put here**:

- User-facing documentation (goes in `/docs` for GitHub Pages)
- Core project documentation (README, CONTRIBUTING, etc. stay in root)
- Code documentation (use docstrings and inline comments)

### Docstring Format

Use Google or NumPy style docstrings:

```python
def start_task(self, project_id: int, template_id: int) -> dict:
    """Start a new task in Semaphore.

    Args:
        project_id: The Semaphore project ID
        template_id: The template ID to run

    Returns:
        dict: Task information including task ID

    Raises:
        aiohttp.ClientError: If API request fails
    """
```

## Deployment

### Supported Platforms

- Primary target: Alpine Linux 3.22+ with Python 3.12+
  - Precompiled binaries avaiable for i686, AMD64, and ARM64, static musl builds
- Other Linux distributions with Python 3.12+ may work
- Docker images available for easy deployment (should also use Alpine base)

### Configuration for Deployment

Configuration is done through `config.json` file with essential settings:

- `matrix.homeserver`: Matrix homeserver URL
- `matrix.user_id`: Bot user ID
- `matrix.auth_type`: Authentication type ("password" or "oidc")
- `matrix.password`: Password (for password auth)
- `matrix.oidc_redirect_url`: Redirect URL (for OIDC auth, optional)
- `semaphore.url`: Semaphore UI URL
- `semaphore.api_token`: Semaphore API token

There is an intial setup process to create the config file if it does not exist built into the bot.

## Common Patterns

### Matrix Room Messaging

```python
await client.room_send(
    room.room_id,
    message_type="m.room.message",
    content={
        "msgtype": "m.text",
        "body": "Message text"
    }
)
```

### Semaphore API Calls

```python
async with self.session.get(
    f"{self.url}/api/project/{project_id}/tasks",
    headers={"Authorization": f"Bearer {self.api_token}"}
) as response:
    response.raise_for_status()
    return await response.json()
```

### Configuration Access

```python
config = Config()
homeserver = config.get("matrix.homeserver")
semaphore_url = config.get("semaphore.url")
```

## Changelog

### Update CHANGELOG.md

**IMPORTANT**: Always update CHANGELOG.md when making code changes. This is a required step for every PR.

When making changes, add entries to the "Unreleased" section of CHANGELOG.md:

```markdown
## [Unreleased]

### Added

- New feature description

### Changed

- Modified behavior description

### Fixed

- Bug fix description
```

**Checklist for every change:**

1. ✅ Make code changes
2. ✅ Update tests
3. ✅ Run tests, iterate until all pass
4. ✅ **Update CHANGELOG.md** (don't forget this!)
5. ✅ Update documentation if needed, including Github Pages (../docs)
6. ✅ Test changes

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 72 characters
- Reference issues: "Fixes #123"

## Plugin System

### Plugin Architecture

ChatrixCD uses a plugin system for extensibility:

- **Plugin Directory**: `plugins/` contains individual plugin folders
- **Plugin Metadata**: Each plugin has `meta.json` with name, description, dependencies
- **Plugin Base Class**: Extend `Plugin` abstract base class from `plugin_manager.py`
- **Plugin Types**: `generic`, `task_monitor`, `command_extension`, etc.
- **Configuration**: Plugin configs stored in separate files, loaded via plugin manager

### Creating Plugins

```python
from chatrixcd.plugin_manager import Plugin, PluginMetadata

class MyPlugin(Plugin):
    async def initialize(self) -> bool:
        # Setup code
        return True

    async def start(self) -> bool:
        # Start functionality
        return True

    async def stop(self):
        # Cleanup
        pass

    async def cleanup(self):
        # Final cleanup
        pass
```

### Plugin Loading

- Plugins loaded automatically from `plugins/` directory
- Dependencies checked before loading
- Plugins initialized in dependency order
- Failed plugins don't break bot startup

## Development Workflows

### Package Management

Use `uv` for fast Python package management:

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/macOS

# Install dependencies
uv pip install -r requirements.txt
uv pip install -e .  # Install in development mode

# Install dev dependencies
uv pip install -e .[dev]
```

### Testing Commands

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest tests.test_config

# Run with coverage (requires pytest-cov)
pytest tests/ --cov=chatrixcd --cov-report=term-missing
```

### Code Quality

```bash
# Format code (requires black)
black --line-length 100 chatrixcd/ tests/

# Lint code (requires flake8)
flake8 chatrixcd/ tests/

# Type check (requires mypy)
mypy chatrixcd/
```

### Running the Bot

```bash
# Interactive TUI mode (default)
chatrixcd

# Log-only mode (for servers/daemons)
chatrixcd -L

# With verbose logging
chatrixcd -vv

# Show configuration and exit
chatrixcd -s

# Initialize/reconfigure
chatrixcd -I
```

## Integration Patterns

### Matrix Protocol Integration

- **Client**: Use `AsyncClient` from matrix-nio for all Matrix operations
- **Events**: Register callbacks for `RoomMessageText`, `InviteMemberEvent`, etc.
- **Encryption**: Automatic Olm/Megolm handling via matrix-nio
- **Authentication**: Support both password and OIDC flows
- **Device Verification**: Implement emoji, QR, and fingerprint verification

### Semaphore API Integration

- **Client**: Custom `SemaphoreClient` class with aiohttp
- **Authentication**: Bearer token in Authorization header
- **SSL**: Configurable certificate validation and client certs
- **Error Handling**: Proper HTTP status code checking and retries
- **Rate Limiting**: Respect API limits with backoff

### TUI Integration

- **Framework**: Textual for terminal UI
- **Screens**: Separate screens for different functions (status, rooms, verification)
- **Widgets**: Custom widgets for bot-specific UI elements
- **Events**: Custom event system for inter-component communication
- **Themes**: Support for multiple color themes

## Additional Resources

- [ARCHITECTURE.md](../docs/architecture.md): Detailed architecture documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md): Contribution guidelines
- [Matrix Protocol Docs](https://matrix.org/docs/): Matrix protocol documentation
- [matrix-nio Docs](https://matrix-nio.readthedocs.io/): Matrix client library docs
- [Semaphore UI Docs](https://docs.ansible-semaphore.com/): Semaphore UI documentation
