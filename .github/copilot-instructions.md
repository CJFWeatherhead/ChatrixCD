# GitHub Copilot Instructions for ChatrixCD

This file provides repository-specific guidance for GitHub Copilot when working with the ChatrixCD project.

## Project Overview

ChatrixCD is a Matrix bot that integrates with Semaphore UI to enable CI/CD automation through chat. The bot supports:
- End-to-end encrypted Matrix rooms
- Multiple authentication methods (password, token, OIDC)
- Asynchronous Python architecture
- Real-time task monitoring and status updates

## Architecture

### Core Components

- **main.py**: Application entry point and lifecycle management
- **config.py**: Configuration management (JSON + environment variables)
- **auth.py**: Matrix authentication handler (password, token, OIDC)
- **bot.py**: Matrix client integration and event handling
- **commands.py**: Command parser and task orchestration
- **semaphore.py**: Semaphore UI REST API client

### Key Technologies

- **matrix-nio**: Matrix protocol client with E2E encryption
- **aiohttp**: Async HTTP client for Semaphore API
- **authlib**: OAuth2/OIDC authentication

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

## Configuration

### Configuration Priority

1. JSON configuration file (`config.json`)
2. Environment variables (uppercase, underscores)
3. Default values

### Accessing Configuration

```python
from chatrixcd.config import Config

config = Config()
matrix_config = config.get_matrix_config()
```

### Environment Variable Naming

- Use SCREAMING_SNAKE_CASE
- Prefix with component: `MATRIX_`, `SEMAPHORE_`, `BOT_`
- Example: `MATRIX_HOMESERVER`, `SEMAPHORE_URL`

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
    def test_load_config_from_env(self):
        """Test configuration loading from environment variables."""
        # Test implementation
        pass
```

### Running Tests

```bash
python -m unittest discover
python -m unittest tests.test_config  # Specific test file
```

### Testing Guidelines

- Mock external services (Matrix server, Semaphore API)
- Test edge cases: empty inputs, None values, errors
- Keep tests isolated and independent
- Write tests for new functionality

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
- Use environment variables for sensitive data in production
- Store encryption keys securely in the `store/` directory
- Never commit `config.json` or `.env` files with real credentials

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
- **ARCHITECTURE.md**: Technical architecture
- **CONTRIBUTING.md**: Development guidelines
- **CHANGELOG.md**: Record of changes

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

- Docker (Debian-based and Alpine Linux)
- Native deployment with systemd (Debian/Ubuntu, RHEL/CentOS, Fedora)
- Native deployment with OpenRC (Alpine Linux)

### Environment Variables for Deployment

Essential environment variables:
- `MATRIX_HOMESERVER`: Matrix homeserver URL
- `MATRIX_USER_ID`: Bot user ID
- `MATRIX_PASSWORD` or `MATRIX_ACCESS_TOKEN`: Authentication
- `SEMAPHORE_URL`: Semaphore UI URL
- `SEMAPHORE_API_TOKEN`: Semaphore API token

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

## Additional Resources

- [ARCHITECTURE.md](../ARCHITECTURE.md): Detailed architecture documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md): Contribution guidelines
- [Matrix Protocol Docs](https://matrix.org/docs/): Matrix protocol documentation
- [matrix-nio Docs](https://matrix-nio.readthedocs.io/): Matrix client library docs
- [Semaphore UI Docs](https://docs.ansible-semaphore.com/): Semaphore UI documentation
