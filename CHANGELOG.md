# Changelog

All notable changes to ChatrixCD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) with format YYYY.MM.PATCH.

## [Unreleased]

### Added

#### Command-Line Interface
- Command-line argument parsing with argparse
- `-V` / `--version` flag to display version information
- `-v` / `-vv` / `-vvv` flags for increasing verbosity levels (INFO, DEBUG, detailed DEBUG with library logs)
- `-h` / `--help` flag for displaying help message (automatically provided by argparse)
- `-c` / `--config` option for specifying alternative configuration file location
- `-C` / `--color` flag for enabling colored logging output (requires colorlog package)
- `-D` / `--daemon` flag for running in daemon mode (background process on Unix/Linux)
- `-s` / `--show-config` flag to display current configuration with redacted credentials
- `-a` / `--admin` option for specifying admin users on command line (can be used multiple times)
- `-r` / `--room` option for specifying allowed rooms on command line (can be used multiple times)
- Configuration overrides via command-line arguments
- Comprehensive tests for CLI argument parsing

#### CI/CD
- GitHub Actions workflow for running unit tests on pull requests
- GitHub Actions workflow for creating releases with calendar versioning
- Automated version bumping in `__init__.py` and `setup.py`
- Automated changelog generation from git commits
- Automated GitHub releases with changelog

### Fixed

#### Encrypted Rooms
- Bot now properly handles encrypted messages by requesting decryption keys when needed
- Added MegolmEvent callback to automatically request room keys for encrypted messages that couldn't be decrypted
- Bot will now respond to commands in encrypted rooms once encryption keys are received

## [0.1.0] - 2024-01-08

### Added

#### Core Features
- Matrix bot implementation using matrix-nio
- End-to-end encryption support for Matrix rooms
- Semaphore UI REST API integration
- Real-time task monitoring and status reporting
- Command-based interface for CI/CD automation

#### Authentication
- Password-based authentication (traditional Matrix)
- Token-based authentication (pre-obtained access tokens)
- OIDC/OAuth2 authentication support with client credentials flow
- Automatic token refresh for OIDC
- Support for OIDC discovery via `.well-known/openid-configuration`

#### Commands
- `!cd help` - Display help message
- `!cd projects` - List available Semaphore projects
- `!cd templates <project_id>` - List templates for a project
- `!cd run <project_id> <template_id>` - Start a task from a template
- `!cd status <task_id>` - Check status of a running task
- `!cd stop <task_id>` - Stop a running task
- `!cd logs <task_id>` - Get logs from a task

#### Configuration
- YAML configuration file support
- Environment variable configuration
- Hierarchical configuration with dot notation access
- Separate configuration sections for Matrix, Semaphore, and bot settings

#### Deployment
- Docker support with Dockerfile
- Docker Compose configuration
- Systemd service file for Linux
- Comprehensive installation guide
- Quick start guide

#### Documentation
- Comprehensive README with features and usage
- Detailed installation guide (INSTALL.md)
- Quick start guide (QUICKSTART.md)
- Architecture documentation (ARCHITECTURE.md)
- Example configuration files

#### Testing
- Unit tests for configuration module
- Test suite using Python unittest

#### Security
- Encryption key storage with configurable path
- Room-based access control (allowed_rooms)
- User-based access control (admin_users)
- Secure credential handling
- No credential logging

### Technical Details

#### Dependencies
- matrix-nio[e2e] >= 0.24.0 - Matrix client with E2E encryption
- aiohttp >= 3.9.0 - Async HTTP client for REST APIs
- PyYAML >= 6.0 - Configuration file parsing

#### Project Structure
```
ChatrixCD/
├── chatrixcd/           # Main package
│   ├── __init__.py      # Package initialization
│   ├── main.py          # Entry point
│   ├── bot.py           # Bot core logic
│   ├── auth.py          # Authentication handlers
│   ├── config.py        # Configuration management
│   ├── commands.py      # Command handlers
│   └── semaphore.py     # Semaphore API client
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
├── setup.py            # Package setup
├── Dockerfile          # Docker image
├── docker-compose.yml  # Docker Compose config
├── chatrixcd.service   # Systemd service
├── README.md           # Main documentation
├── INSTALL.md          # Installation guide
├── QUICKSTART.md       # Quick start guide
├── ARCHITECTURE.md     # Architecture docs
└── CHANGELOG.md        # This file
```

#### Key Implementation Details

**OIDC Authentication Flow**:
1. Discover OIDC endpoints from issuer
2. Use client credentials grant to obtain token
3. Set token on Matrix client
4. Verify token with sync request
5. Support token refresh when available

**Task Monitoring**:
- Async background task for each running job
- Polls Semaphore API every 10 seconds
- Sends status updates to Matrix room
- Automatically removes completed tasks

**E2E Encryption**:
- Automatic key storage in configurable directory
- Support for encrypted rooms
- Device management via matrix-nio

### Security Considerations
- Credentials stored in configuration files or environment variables
- Access tokens not logged
- Support for restrictive file permissions
- Room and user access controls
- Secure OIDC implementation with HTTPS-only endpoints

### Platform Support
- Linux (tested)
- macOS (should work)
- Windows (should work)
- Docker (Linux containers)

### Known Limitations
- No interactive task parameter input yet
- No task scheduling support
- Single Semaphore instance per bot
- In-memory task tracking (lost on restart)
- No web interface

### Future Plans
- Interactive task configuration
- Task scheduling with cron syntax
- Multi-tenant support
- Webhook support for push notifications
- Rich message formatting
- Task history and analytics
- Admin dashboard

## [Unreleased]

### Planned
- Add tests for authentication module
- Add tests for Semaphore client
- Add tests for command handler
- Add integration tests
- Add CI/CD pipeline for the bot itself
- Add health check endpoint
- Add metrics collection
- Add performance benchmarks

---

## Version History

- **0.1.0** (2024-01-08) - Initial release with OIDC support
