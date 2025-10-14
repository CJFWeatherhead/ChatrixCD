<div align="center">

<img src="assets/logo-horizontal.svg" alt="ChatrixCD Logo" width="600">

# ChatrixCD

**Matrix bot for CI/CD automation through chat**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-4A9B7F)](https://cjfweatherhead.github.io/ChatrixCD/)

---

</div>

ChatrixCD integrates with Semaphore UI to enable CI/CD automation through chat. It supports end-to-end encrypted Matrix rooms and provides password and OIDC/SSO authentication for Matrix servers.

## Documentation

📚 **[Full Documentation](https://cjfweatherhead.github.io/ChatrixCD/)** - Installation guides, configuration reference, architecture overview, and more.

## Features

- 🔐 **Native Matrix Authentication**: Support for password and OIDC/SSO authentication with Matrix servers
- 🔒 **E2E Encryption**: Full support for end-to-end encrypted Matrix rooms with device verification
- 🖥️ **Interactive TUI**: Text User Interface for bot management, monitoring, and configuration
- 🚀 **Semaphore UI Integration**: Start and monitor CI/CD tasks via chat commands
- 📊 **Real-time Updates**: Automatic status updates for running tasks
- 🎯 **Command-based Interface**: Easy-to-use command system for task management
- 🔧 **Flexible Configuration**: Support for HJSON config files (JSON with comments) with automatic migration
- ✅ **Configuration Validation**: Built-in schema validation with clear error messages
- 🔄 **Auto-Migration**: Automatic upgrade of configuration files when new features are added

## Installation

### Prerequisites

- Python 3.9 or higher
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

ChatrixCD is configured using JSON configuration files with HJSON support.

**HJSON Configuration (JSON with Comments)**

Configuration files support HJSON format, which allows comments and trailing commas for better documentation:

1. Copy the example configuration file:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` with your settings (comments are supported):
   ```hjson
   {
     // Configuration file version
     "_config_version": 2,
     
     // Matrix homeserver settings
     "matrix": {
       "homeserver": "https://matrix.example.com",  // Your Matrix server
       "user_id": "@chatrixcd:example.com",         // Bot user ID
       "auth_type": "password",                      // or "oidc"
       "password": "your_password"
     },
     
     // Semaphore UI settings
     "semaphore": {
       "url": "https://semaphore.example.com",
       "api_token": "your_semaphore_api_token"
     },
     
     // Bot behavior
     "bot": {
       "command_prefix": "!cd"
     }
   }
   ```

**Configuration Priority**: Configuration file values have highest priority, followed by hardcoded defaults.

**Configuration Migration**: Old configuration files are automatically migrated to the current version. A backup is created before migration.

## Authentication Methods

ChatrixCD supports two authentication methods for Matrix:

### 1. Password Authentication (Recommended for most users)

Traditional username/password authentication:

```json
{
  "matrix": {
    "auth_type": "password",
    "user_id": "@chatrixcd:example.com",
    "password": "your_password"
  }
}
```

### 2. OIDC/SSO Authentication (For OIDC-enabled servers)

For Matrix servers using OIDC/Single Sign-On:

```json
{
  "matrix": {
    "auth_type": "oidc",
    "user_id": "@chatrixcd:example.com"
  }
}
```

**OIDC Authentication Flow:**
1. When you start the bot, it will display an SSO URL
2. Open the URL in your browser and complete authentication
3. After authentication, copy the callback URL (containing `loginToken`)
4. Paste the URL or token back into the bot
5. The bot completes login automatically

**Optional Configuration:**
- `oidc_redirect_url`: The URL where your browser will be redirected after authentication (defaults to `http://localhost:8080/callback`)
  - Does **not** need to be a running web server
  - Only used to receive the `loginToken` in the URL
  - For most users, the default is sufficient

## Usage

### Starting the Bot

**Interactive Mode (TUI):**

By default, when running ChatrixCD interactively in a terminal, it will launch with a Text User Interface (TUI):

```bash
chatrixcd
```

The TUI provides a menu-driven interface with options for:
- **STATUS** - View bot status (Matrix/Semaphore connections, uptime, metrics)
- **ADMINS** - View admin users
- **ROOMS** - View joined rooms
- **SESSIONS** - Manage Olm encryption sessions
- **SAY** - Send messages to rooms
- **LOG** - View bot logs
- **SET** - Change operational variables
- **SHOW** - View current configuration
- **QUIT** - Gracefully exit

**Classic Log Mode:**

To run without the TUI (classic log-only mode):

```bash
chatrixcd -L
```

Or if running from source:

```bash
python -m chatrixcd.main -L
```

**Daemon Mode:**

To run as a background process:

```bash
chatrixcd -D
```

### Command-Line Options

ChatrixCD supports various command-line options for configuration and control:

```bash
chatrixcd [OPTIONS]
```

**Options:**

- `-h, --help` - Show help message and exit
- `-V, --version` - Show version number and exit
- `-v, --verbose` - Increase verbosity (use `-v` for DEBUG, `-vv` for detailed DEBUG with library logs)
- `-c FILE, --config FILE` - Path to configuration file (default: config.json)
- `-C, --color` - Enable colored logging output in TUI and logs (requires colorlog package)
- `-R, --redact` - Redact sensitive information from logs (room names, usernames, IPs, tokens, etc.)
- `-L, --log-only` - Run in classic log-only mode (no TUI, only show logs)
- `-D, --daemon` - Run in daemon mode (background process, Unix/Linux only)
- `-s, --show-config` - Display current configuration with redacted credentials and exit
- `-a USER, --admin USER` - Add admin user (can be specified multiple times)
- `-r ROOM, --room ROOM` - Add allowed room (can be specified multiple times)

**Examples:**

```bash
# Show version
chatrixcd --version

# Run with interactive TUI (default)
chatrixcd

# Run with interactive TUI and colored output
chatrixcd -C

# Run in classic log-only mode (no TUI)
chatrixcd -L

# Use custom config file with verbose logging
chatrixcd -c /etc/chatrixcd/config.json -v -L

# Run in daemon mode (automatically disables TUI)
chatrixcd -D

# Show current configuration
chatrixcd -s

# Override admin users and allowed rooms
chatrixcd -a @admin1:matrix.org -a @admin2:matrix.org -r !room1:matrix.org

# Combine multiple options with TUI
chatrixcd -v -C -c custom.json -a @admin:matrix.org

# Enable verbose logging with redaction for privacy (recommended for bug reports)
chatrixcd -vv -R -L

# Redaction with colored output (redacted content appears in pink)
chatrixcd -vv -C -R -L
```

**Privacy Note**: When reporting bugs or sharing logs, use the `-R` flag to automatically redact sensitive information like room IDs, usernames, IP addresses, and tokens. When combined with `-C`, redacted information will be highlighted in pink for easy identification.

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

## Deployment

ChatrixCD supports multiple deployment options:

### Docker Deployment

**Debian-based (default)**:
```bash
docker build -t chatrixcd .
docker run -d --name chatrixcd \
  -v $(pwd)/store:/app/store \
  -e MATRIX_HOMESERVER=https://matrix.example.com \
  -e MATRIX_USER_ID=@chatrixcd:example.com \
  -e MATRIX_PASSWORD=your_password \
  chatrixcd
```

**Alpine Linux (minimal)**:
```bash
docker build -f Dockerfile.alpine -t chatrixcd:alpine .
docker run -d --name chatrixcd \
  -v $(pwd)/store:/app/store \
  -e MATRIX_HOMESERVER=https://matrix.example.com \
  chatrixcd:alpine
```

### Native Deployment

- **Debian/Ubuntu**: Use `chatrixcd-debian.service` with systemd
- **RHEL/CentOS/Fedora**: Use `chatrixcd.service` with systemd
- **Alpine Linux**: Use `chatrixcd.initd` with OpenRC

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed comparison and [INSTALL.md](INSTALL.md) for complete instructions.

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
- **Credentials**: Never commit your `config.json` file with real credentials.
- **Access Control**: Use `allowed_rooms` and `admin_users` to restrict bot access.
- **API Tokens**: Use Semaphore API tokens with minimal required permissions.

## Development

### Running Tests

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate    # On Windows

# Install dependencies and test tools
uv pip install -r requirements.txt
uv pip install pytest pytest-cov pytest-asyncio

# Run tests with coverage
pytest tests/ --cov=chatrixcd --cov-report=term-missing
```

#### Test Coverage

Current test coverage:
- **config.py**: 89% - Configuration loading and management
- **auth.py**: 38% - Authentication methods (password, token, OIDC)
- **semaphore.py**: 23% - Semaphore API client basics
- **Overall**: 16% - Basic unit tests for core modules

Tests cover:
- Configuration from JSON and environment variables
- Password, token, and OIDC authentication flows
- Semaphore client initialization
- Error handling for missing configurations

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
│   ├── semaphore.py    # Semaphore API client
│   ├── tui.py          # Text User Interface
│   └── redactor.py     # Sensitive data redaction
├── requirements.txt
├── setup.py
├── config.json.example
└── README.md
```

## CI/CD

### Automated Testing

Pull requests are automatically tested using GitHub Actions. Tests run against Python 3.9, 3.10, 3.11, and 3.12.

### Releases

Releases use a semantic calendar versioning system with the format `YYYY.MM.DD.MAJOR.MINOR.PATCH` (e.g., `2025.10.12.1.0.1`).

**Version Format:**
- `YYYY.MM.DD`: Release date (year, month, day)
- `MAJOR`: Breaking changes or major features
- `MINOR`: New features, non-breaking changes
- `PATCH`: Bug fixes and security updates

**Important:** Version numbers (MAJOR, MINOR, PATCH) always increment and never reset. This ensures each version is unique and comparable.

To create a new release:

1. Go to Actions → Build and Release workflow
2. Click "Run workflow"
3. Select version type:
   - **major**: Breaking changes or major features (e.g., 2025.10.12.1.0.1 → 2025.10.13.2.0.0)
   - **minor**: New features, non-breaking (e.g., 2025.10.12.1.0.1 → 2025.10.13.1.1.0)
   - **patch**: Bug fixes and security updates (e.g., 2025.10.12.1.0.1 → 2025.10.13.1.0.2)

4. The workflow will:
   - Run all unit tests
   - Calculate the new version based on current date and type
   - Update version in code (`__init__.py` and `setup.py`)
   - Update `CHANGELOG.md` (move Unreleased content to new version section)
   - Generate changelog from commits
   - Commit all changes
   - Create a GitHub release

**Note**: Document changes in the `[Unreleased]` section of `CHANGELOG.md` as you develop. The release workflow will automatically move these changes to a versioned section.

**Historical Note**: Versions prior to October 2025 used the format `YYYY.MM.PATCH` (e.g., `2025.10.8`). The new format provides better semantic versioning while maintaining date-based organization.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct, development process, and how to submit pull requests.

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Issue Templates](.github/ISSUE_TEMPLATE/)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [matrix-nio](https://github.com/poljar/matrix-nio)
- Integrates with [Semaphore UI](https://github.com/ansible-semaphore/semaphore)
- Inspired by [matrix-commander](https://github.com/8go/matrix-commander) for device verification and encryption handling patterns

### AI/LLM Contributions

**Important Notice:** Significant portions of this codebase were developed with assistance from AI/LLM tools, including:
- GitHub Copilot for code generation and completion
- Large Language Models (LLMs) for architecture design, documentation, and implementation
- AI-assisted code review and testing strategies

While AI tools accelerated development, all code has been reviewed, tested, and validated by human developers. Users should be aware that:
- Code patterns and documentation may reflect AI-generated content
- The project follows standard software engineering practices for testing and quality assurance
- Contributions and improvements from the community are welcome and encouraged

This transparency aligns with emerging best practices for AI-assisted software development.
