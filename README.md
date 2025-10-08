# ChatrixCD

A Matrix bot that integrates with Semaphore UI to enable CI/CD automation through chat. ChatrixCD supports end-to-end encrypted rooms and provides OIDC/token-based authentication for Matrix servers.

## Features

- 🔐 **OIDC Authentication**: Support for OIDC/OAuth2 and token-based authentication with Matrix servers
- 🔒 **E2E Encryption**: Full support for end-to-end encrypted Matrix rooms
- 🚀 **Semaphore UI Integration**: Start and monitor CI/CD tasks via chat commands
- 📊 **Real-time Updates**: Automatic status updates for running tasks
- 🎯 **Command-based Interface**: Easy-to-use command system for task management
- 🔧 **Flexible Configuration**: Support for both YAML config files and environment variables

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- Access to a Matrix homeserver
- Access to a Semaphore UI instance with API access

### Install from source

```bash
# Clone the repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Install the application
uv pip install -e .
```

## Configuration

ChatrixCD can be configured using either a YAML configuration file or environment variables.

### Using YAML Configuration

1. Copy the example configuration file:
   ```bash
   cp config.yaml.example config.yaml
   ```

2. Edit `config.yaml` with your settings:
   ```yaml
   matrix:
     homeserver: "https://matrix.example.com"
     user_id: "@chatrixcd:example.com"
     auth_type: "password"  # or "token" or "oidc"
     password: "your_password"  # for password auth
     
   semaphore:
     url: "https://semaphore.example.com"
     api_token: "your_semaphore_api_token"
     
   bot:
     command_prefix: "!cd"
   ```

### Using Environment Variables

1. Copy the example .env file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings

## Authentication Methods

ChatrixCD supports three authentication methods for Matrix:

### 1. Password Authentication (Traditional)

```yaml
matrix:
  auth_type: "password"
  user_id: "@chatrixcd:example.com"
  password: "your_password"
```

### 2. Token Authentication (Pre-obtained)

If you have a pre-obtained access token:

```yaml
matrix:
  auth_type: "token"
  user_id: "@chatrixcd:example.com"
  access_token: "your_access_token"
```

### 3. OIDC Authentication (Recommended for OIDC-enabled servers)

For Matrix servers using OIDC/OAuth2:

```yaml
matrix:
  auth_type: "oidc"
  user_id: "@chatrixcd:example.com"
  oidc_issuer: "https://auth.example.com"
  oidc_client_id: "your_client_id"
  oidc_client_secret: "your_client_secret"
```

## Usage

### Starting the Bot

```bash
chatrixcd
```

Or if running from source:

```bash
python -m chatrixcd.main
```

### Bot Commands

Once the bot is running and invited to a room, you can use the following commands:

- `!cd help` - Show help message with available commands
- `!cd projects` - List all available Semaphore projects
- `!cd templates <project_id>` - List templates for a specific project
- `!cd run <project_id> <template_id>` - Start a task from a template
- `!cd status <task_id>` - Check the status of a running task
- `!cd stop <task_id>` - Stop a running task
- `!cd logs <task_id>` - Get logs from a task

### Example Workflow

1. Invite the bot to your Matrix room
2. List available projects:
   ```
   !cd projects
   ```
3. View templates for a project:
   ```
   !cd templates 1
   ```
4. Start a task:
   ```
   !cd run 1 5
   ```
5. The bot will automatically report status updates as the task runs

## Architecture

ChatrixCD is built with the following components:

- **matrix-nio**: Async Python Matrix client library with E2E encryption
- **authlib**: OAuth2/OIDC authentication library
- **aiohttp**: Async HTTP client for Semaphore UI API calls

### Key Components

- `bot.py` - Main bot logic and Matrix client integration
- `auth.py` - Authentication handler with OIDC support
- `semaphore.py` - Semaphore UI REST API client
- `commands.py` - Command parser and handler
- `config.py` - Configuration management

## Security Considerations

- **Encryption Keys**: The bot stores encryption keys in the configured `store_path` directory. Keep this secure.
- **Credentials**: Never commit your `config.yaml` or `.env` file with real credentials.
- **Access Control**: Use `allowed_rooms` and `admin_users` to restrict bot access.
- **API Tokens**: Use Semaphore API tokens with minimal required permissions.

## Development

### Running Tests

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate    # On Windows

# Install test dependencies
uv pip install -r requirements.txt

# Run tests (when available)
pytest
```

### Project Structure

```
ChatrixCD/
├── chatrixcd/
│   ├── __init__.py
│   ├── main.py         # Entry point
│   ├── bot.py          # Bot core
│   ├── auth.py         # Authentication
│   ├── config.py       # Configuration
│   ├── commands.py     # Command handlers
│   └── semaphore.py    # Semaphore API client
├── requirements.txt
├── setup.py
├── config.yaml.example
├── .env.example
└── README.md
```

## CI/CD

### Automated Testing

Pull requests are automatically tested using GitHub Actions. Tests run against Python 3.8, 3.9, 3.10, and 3.11.

### Releases

Releases are created using a calendar versioning (CalVer) system with the format `YYYY.MM.PATCH` (e.g., `2024.12.0`).

To create a new release:

1. Go to Actions → Build and Release workflow
2. Click "Run workflow"
3. Select version type:
   - **patch**: Increment patch version (e.g., 2024.12.0 → 2024.12.1)
   - **minor**: Increment patch version for new features (e.g., 2024.12.0 → 2024.12.1)
4. The workflow will:
   - Run all unit tests
   - Calculate the new version based on current date
   - Update version in code
   - Generate changelog from commits
   - Create a GitHub release with the changelog

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [matrix-nio](https://github.com/poljar/matrix-nio)
- Integrates with [Semaphore UI](https://github.com/ansible-semaphore/semaphore)
