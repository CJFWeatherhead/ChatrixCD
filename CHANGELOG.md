# Changelog

All notable changes to ChatrixCD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) with format YYYY.MM.PATCH.

## [Unreleased]

### Added
- **SSL/TLS Configuration for Semaphore**: Added flexible SSL/TLS options for Semaphore connections
  - `ssl_verify`: Enable/disable SSL certificate verification (default: true)
  - `ssl_ca_cert`: Path to custom CA certificate bundle for custom/internal CAs
  - `ssl_client_cert`: Path to client certificate for mutual TLS (mTLS) authentication
  - `ssl_client_key`: Path to client certificate private key
  - Resolves issues connecting to Semaphore with self-signed certificates
  - Supports enterprise environments with custom certificate authorities
  - Enables mutual TLS authentication when required
  - Configuration options documented in docs/configuration.md
  - Added tests for SSL configuration options

### Fixed
- **E2E Encryption Session Management**: Fixed issues with encrypted message decryption
  - Bot now automatically uploads device keys and one-time keys after login
  - Bot queries device keys from other users to establish Olm sessions
  - Prevents duplicate room key requests by tracking requested session IDs
  - Automatic key management after each sync to maintain encryption state
  - Resolves "A key sharing request is already sent out" error
  - Improves reliability of encryption in encrypted rooms

## [2025.10.7] - 2025-10-09

### Breaking Changes
- **Removed Environment Variable Support**: Configuration is now exclusively loaded from JSON files
  - Environment variables are no longer supported for configuration
  - All configuration must be specified in `config.json`
  - This simplifies configuration management and eliminates confusion about configuration sources
  - Existing deployments using environment variables need to migrate to JSON configuration files

### Added
- **HJSON Support**: Configuration files now support HJSON (Human JSON) format
  - Add comments to configuration files using `//`, `/* */`, or `#`
  - Trailing commas are now allowed in configuration files
  - Full backward compatibility with existing JSON files
  - Added `hjson` dependency to requirements.txt
  - Updated `config.json.example` with extensive inline comments

### Changed
- **Configuration System Simplified**: Configuration is now exclusively file-based
  - Configuration file values have highest priority
  - Hardcoded defaults used as fallback when not in file
  - Environment variables no longer affect configuration
  - More predictable and explicit configuration behavior
- **Configuration Loading**: Simplified configuration system
  - Removed `_apply_env_overrides()` method
  - Cleaner separation between defaults and file values
  - Better error messages for configuration parsing failures

### Fixed
- **Configuration File Loading**: Fixed issue where configuration file values could be ignored
  - Resolves reported issue where JSON parameters were not being parsed correctly
  - User ID and other configuration values are now reliably loaded from config.json

### Improved
- **Configuration Documentation**: Updated documentation to reflect JSON-only configuration
  - Removed references to environment variables throughout documentation
  - Clarified configuration priority system (file > defaults)
  - Updated examples to show JSON-only configuration
  - Updated security best practices for managing secrets in JSON files
- **Test Coverage**: Updated tests to verify environment variables are ignored
  - Added tests to verify environment variables don't affect configuration
  - All 114 tests passing

## [2025.10.6] - 2025-10-09

### Breaking Changes
- **Removed YAML Configuration Support**: Configuration files must now be in JSON format
  - YAML support has been completely removed to simplify the codebase and reduce dependencies
  - Existing YAML configurations need to be converted to JSON format (see `config.json.example`)
  - PyYAML dependency removed from requirements
  - Default configuration file changed from `config.yaml` to `config.json`

### Fixed
- **Configuration Merge Bug**: Fixed shallow copy bug in `_merge_configs()` that could cause configuration corruption
  - Now uses `copy.deepcopy()` to properly copy nested dictionaries
  - Ensures defaults are not modified during merge operations
  - Prevents potential configuration state leakage between loads

### Added

#### Configuration System Improvements
- **Configuration Versioning**: Implemented configuration schema versioning system
  - Current version: 2
  - Automatic detection of configuration version
  - Backward compatibility with version 1 (implicit) configurations
- **Automatic Configuration Migration**: Old configurations are automatically migrated to the current version
  - Preserves all existing settings during migration
  - Creates backup of original file (`.backup` extension)
  - Saves migrated configuration back to disk
  - Seamless upgrade path for new features
- **Configuration Validation**: Added schema validation with detailed error reporting
  - Validates required fields (homeserver, user_id, semaphore URL, etc.)
  - Checks authentication configuration completeness
  - Validates auth_type values
  - Returns clear error messages for missing or invalid fields
- **Configuration Version API**: Added `get_config_version()` method to query current config version
- **JSON Example**: Added `config.json.example` with fully documented JSON configuration format

### Improved
- **Configuration Documentation**: Enhanced documentation for JSON-only configuration
  - Configuration versioning explanation
  - Migration process documentation
  - Validation documentation
  - JSON troubleshooting
- **Error Handling**: JSON parse errors show exact line and column numbers for easy debugging

### Fixed (Historical)
- Fixed configuration loading to properly apply default values when config file exists but doesn't specify all fields. Previously, missing fields would be `None` instead of using defaults, causing "User id is not set" errors with token authentication.

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

### Improved
- **Configuration Error Handling**: Added graceful handling of malformed JSON configuration files
  - Clear error messages showing filename, line number, and column where error occurred
  - Detailed problem description for JSON parsing errors
  - Proper error messages for file permission issues
  - Bot exits with status code 1 on configuration errors instead of crashing with stack trace

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



- **2025.10.7** (2025-10-09)
- **2025.10.6** (2025-10-09)
- **0.1.0** (2024-01-08) - Initial release with OIDC support
