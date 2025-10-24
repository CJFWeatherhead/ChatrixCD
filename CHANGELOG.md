# Changelog

All notable changes to ChatrixCD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Calendar Versioning with format YYYY.MM.DD.MAJOR.MINOR.PATCH.

**Version Format:**
- `YYYY.MM.DD`: Release date
- `MAJOR`: Breaking changes or major features
- `MINOR`: New features, non-breaking
- `PATCH`: Bug fixes and security updates

**Historical Note**: Versions prior to October 2025 used format `YYYY.MM.PATCH` (e.g., `2025.10.8`).

## [Unreleased]

### Fixed
- **Build and Release Workflow**: Fixed multiple critical build failures
  - Updated Nuitka Action to use `mode=onefile` instead of deprecated `onefile/standalone` options
  - Added QEMU setup for ARM64 cross-compilation on Linux
  - Installed libolm build dependency via homebrew on macOS
  - Setup CMake and libolm build environment on Windows
  - Fixed compatibility issues with python-olm native extension builds

### Added
- **Configuration Wizard**: Interactive configuration setup with `--init` flag
  - Console-based wizard for creating/updating configuration
  - Parses `config.json.example` for field descriptions and defaults
  - Automatic config wizard prompt when `config.json` is missing
  - Creates backups before overwriting existing configs
  - Supports all config sections: Matrix, Semaphore, and Bot settings
- **--no-greetings Flag**: New `-N/--no-greetings` command-line flag to skip startup/shutdown messages (useful for testing)
- **Enhanced Bot Personality**: More sassy and fun responses throughout
  - 20 greeting variations with name-first style for extra personality
  - More varied and expressive timeout, cancellation, and task execution messages
  - Sassy admin rejection messages
  - Fun ping/pong responses
- **PyYAML Dependency**: Added PyYAML to requirements.txt for workflow configuration tests
- **Task Completion Notifications**: Users who initiate tasks are now notified when their task completes
  - Personalized completion messages addressing the user by name
  - Success notifications with party emoji 🎉
  - Failure notifications with clear status indication
- **Message Customization System**: Externalized bot response messages for easy customization
  - New `messages.json` file for all bot responses (greetings, confirmations, timeouts, etc.)
  - `messages.json.example` provided as template
  - MessageManager class handles loading and formatting messages
  - Custom messages override defaults while preserving fallback behavior
  - Hot-reload support: changes take effect without restarting bot
- **Asynchronous File Watching**: Config files now auto-reload when modified
  - `config.json` auto-reloads every 10 seconds
  - `aliases.json` auto-reloads every 5 seconds  
  - `messages.json` auto-reloads every 5 seconds
  - Changes take effect without bot restart
  - Thread-safe implementation using asyncio tasks

### Changed
- **Configuration Migration**: Migration system now suggests running `--init` after automatic migration to review new settings
- **Username Display**: User display names now keep the `@` symbol for proper Matrix user identification
- **Version Calculation System**: Complete refactoring for simplicity and robustness
  - Created centralized version calculation script (`.github/scripts/calculate-version.sh`)
  - Eliminated 269 lines of duplicate code across build jobs (32.5% reduction in workflow file size)
  - Single source of truth for version logic - easier to maintain and debug
  - Simplified workflow from 4 duplicate implementations to 4 calls to one script
  - Automatic fallback to patch increment for empty/unknown version types
  - Consistent behavior across all build platforms (Linux, Windows, macOS)
- **Bot Response Architecture**: Refactored command handler to use MessageManager
  - Removed hardcoded message lists from commands.py
  - All response messages now managed through MessageManager
  - Improved testability with injectable message configurations

### Fixed
- **TUI CSS Error**: Fixed `$foreground` variable undefined error in Textual 6.x
  - Added `foreground` CSS variable to both `tui.py` and `tui_turbo.py`
  - Aliased to `text` color for compatibility
- **Reaction Parsing**: Fixed reaction confirmation handling
  - Strip Unicode variation selectors (0xFE00-0xFE0F) from emoji for proper matching
  - Reactions like 👍️ with variation selectors now work correctly
- **Command Response Formatting**: Fixed concatenated response messages
  - Added missing commas in all response arrays (greetings, timeouts, cancellations, etc.)
  - Commands like `!cd exit`, `!cd pet`, `!cd scold` now send single random responses instead of concatenated strings
- **Build and Release Workflow**: Comprehensive fixes for build process failures
  - Fixed invalid `grep -v '\-dev$'` pattern causing "invalid argument" errors (changed to `grep -v -- '-dev$'`)
  - Added missing `git fetch --tags --force` step to Windows and macOS build jobs for complete tag history
  - Removed Windows ARM64 build from matrix (not feasible on GitHub Actions x86_64 runners)
  - All version calculation scripts now work correctly across all build jobs
  - Ensures consistent version calculation and proper tag handling

### Removed
- **Threaded Responses**: Completely removed all threading functionality for conventional message handling
  - All bot responses now sent as regular messages instead of thread replies
  - Removed thread detection logic from message callback
  - Simpler conversation flow without threading complexity
  - Better compatibility with various Matrix clients
- **!cda Command Mode**: Removed non-threaded command prefix as it's now redundant
  - Only `!cd` command prefix is supported
  - Help text updated to remove `!cda` references

### Fixed
- **Build Process**: Fixed test failures in CI/CD pipeline
  - Added missing PyYAML dependency for test_workflow.py
  - Resolved ModuleNotFoundError for yaml module in tests
- **Reaction Processing**: Improved reaction handling for more consistent processing
  - Reactions for confirmations work reliably
  - Positive reactions (👍, ✅, etc.) and negative reactions (👎, ❌, etc.) properly recognized
- **!cd log Command**: Verified log command functionality is working correctly
  - One-time log retrieval with `!cd log [task_id]`
  - Real-time log tailing with `!cd log on/off`
  - Proper error messages for missing tasks

### Added (Previous Features)
- **Configuration Version 4**: Expanded configuration options with comprehensive settings
  - Added `bot.mouse_enabled` for configurable mouse support in TUI
  - Added `bot.color_enabled` for enabling colored output (overridable with -C flag)
  - Added `bot.color_theme` with 5 theme options: 'default', 'midnight', 'grayscale', 'windows31', 'msdos'
    - **default**: ChatrixCD brand colors (green #4A9B7F)
    - **midnight**: Midnight Commander-style blue/cyan terminal theme
    - **grayscale**: Monochrome theme for accessibility
    - **windows31**: Windows 3.1-inspired gray/blue vintage theme
    - **msdos**: MS-DOS-style amber/green on black retro terminal theme
  - Added `bot.verbosity` with levels: 'silent', 'error', 'info', 'debug' (overridable with -v flags)
  - Themes work with both Turbo Vision and Classic TUI modes
- **Automatic Configuration Migration**: V3 to V4 migration for seamless upgrades
- **Turbo Vision-Style TUI**: New classic TUI interface inspired by Turbo Vision
  - Menu bar at the top with File, Edit, Run, Help menus
  - 3D windowed appearance with drop shadows using box-drawing characters
  - Status bar at bottom showing task status ("Idle" or "Running X task(s)")
  - ChatrixCD brand colors (#4A9B7F green) throughout the interface
  - Logical menu organization based on functionality
  - All features from original TUI are available
- **Reaction-Based Confirmations**: Quick interaction with emoji reactions
  - Users can confirm actions with 👍 (thumbs up) or 👎 (thumbs down)
  - No need to type "yes" or "no" - just react to the confirmation message
  - Reactions are processed instantly for faster workflow
- **Enhanced Bot Personality**: Sassy and fun responses with emoji
  - Personalized greetings addressing users by name (e.g., "username 👋")
  - 16 varied greeting options: Hi, Hello, Yo, Sup, Howdy, Hiya, Heya, G'day, Greetings, Welcome, Ahoy, Salutations, Hey there, What's up
  - Varied and engaging response messages throughout commands
  - Emoji-rich messages for better visual appeal
- **Async Log Tailing**: Enhanced `!cd log` command with real-time log streaming
  - `!cd log on` - Start tailing logs for the last task with real-time updates
  - `!cd log off` - Stop tailing logs
  - `!cd log <task_id>` - Get logs for a specific task (one-time)
  - `!cd log` - Get logs for the last task (one-time, existing behavior)
  - Log updates sent every 5 seconds while task is running
  - Automatic stop when task completes with final logs
  - Logs properly formatted with ANSI color codes converted to HTML
- **Enhanced Logging for Debugging**: Comprehensive logging of bot actions
  - Log when bot receives commands with full details
  - Log command parameter resolution (auto-selection of projects/templates)
  - Log all bot responses for easier debugging
  - Command execution flow logged at each step

### Changed
- Default TUI is now the Turbo Vision-style interface (`tui_turbo`)
- Original TUI is still available and can be selected via configuration
- Bot responses are more conversational and engaging
- Configuration file version updated to 4
- Command-line flags now properly override config file settings for color, mouse, and verbosity
- TUI themes now properly applied with correct text/background contrast
- Both classic and turbo TUI support all 5 color themes

### Fixed
- **TUI Theme Support**: Fixed theme implementation in both TUI modes
  - Themes now properly passed to TUI initialization
  - Added `get_css_variables()` method for dynamic theme application
  - Fixed text visibility issues with proper color contrast in all themes
  - Resolved issue where turbo TUI default scheme had text same color as background

## [2025.10.18.3.1.0] - 2025-10-18

No changes recorded.

## [2025.10.17.3.0.0] - 2025-10-17

### Fixed
- **Bot Not Responding to Encrypted Messages**: Fixed critical issue where bot could decrypt messages but wouldn't respond to commands
  - Fixed `server_timestamp` attribute missing on decrypted events causing AttributeError
  - Added logic to copy timestamp from MegolmEvent to decrypted RoomMessageText before processing
  - Ensures old message filtering works correctly for encrypted messages
  - Added comprehensive tests for encrypted message timestamp handling
- **End-to-End Encryption Improvements**: Major improvements to encryption handling and device verification
  - Fixed TUI to properly display user ID and device ID in verification requests (was showing "Unknown")
  - Proactively query device keys when receiving undecryptable messages
  - Automatically establish Olm sessions by claiming one-time keys before requesting room keys
  - Send to-device messages after room key requests to ensure delivery
  - Track requested sessions per sender to prevent duplicate key requests
  - Handle duplicate key request errors gracefully (matrix-nio internally prevents duplicates)
  - Add session tracking before request to prevent race conditions
  - Proactively query device keys for all users in encrypted rooms during sync
  - Perform initial encryption setup after first sync (query keys and establish sessions)
  - Share room keys with devices immediately after successful verification
  - Improved error recovery for decryption failures with automatic session establishment

### Added
- **Verification Status Persistence**: Device verification status is now persisted across restarts
  - Verified devices are automatically saved to the encryption store
  - `get_verified_devices()` method to retrieve list of verified devices
  - `is_device_verified()` method to check verification status of specific devices
  - Verification state is maintained even after bot restarts
  - Added 9 new comprehensive tests for verification persistence

### Fixed
- **Device Verification**: Fixed timeout issues when verifying devices
  - Verification requests now properly display user ID and device ID instead of "Unknown"
  - Verification accept/start messages are now correctly sent to other devices
  - Added `send_to_device_messages()` calls after verification operations
  - Fixed `get_pending_verifications()` to extract device info from `Sas.other_olm_device`

### Added
- **Comprehensive E2E Verification Tests**: Added 10 new end-to-end tests for device verification
  - Full verification flow test from start to finish
  - Auto-verification flow test for daemon mode
  - Interactive verification flow tests (accept/reject scenarios)
  - Tests for proper user_id and device_id extraction
  - Tests for to-device message sending

## [2025.10.17.2.0.0] - 2025-10-17

### Added
- **Command Aliases**: Create custom shortcuts for frequently used commands
  - Manage aliases through the TUI (press `x` in main menu) or edit `aliases.json` file
  - Aliases stored separately from `config.json` for easy management
  - Only valid `!cd` commands can be aliased
  - Example: Create `deploy-prod` alias for `run 1 5`
- **Task Confirmation**: Required confirmation before executing tasks
  - Shows task name and description before running
  - Confirmation required with `y`, `yes`, `go`, `start`, or similar
  - Prevents accidental task execution
- **Smart Parameter Handling**: Auto-fill project/template IDs when only one option available
  - `!cd templates` auto-selects project if only one exists
  - `!cd run` auto-selects project/template if only one option
  - Prompts for clarification when ambiguous
- **Enhanced Status and Logs Commands**: Can be used without task ID
  - `!cd status` uses last task run if no ID provided
  - `!cd logs` uses last task run if no ID provided
  - Remembers the most recently started task
- **Rich Message Formatting**: Markdown and HTML formatting support
  - Bold text with `**text**` renders properly
  - Italic, code blocks, and lists supported
  - Emoji support throughout all commands
- **Improved Log Output**: Better formatting and parsing
  - Detects Ansible and Terraform output formats
  - Removes ANSI color codes for clean display
  - Tails last 100 lines to avoid truncation
  - Shows line count when truncated
- **Periodic Task Updates**: Long-running tasks send status reminders
  - "Task xyz is still running" message every 5 minutes
  - Prevents tasks from being forgotten
- **Task Naming**: Tasks displayed with name and ID
  - Format: "Template Name (123)" instead of just "123"
  - Fetches template names from Semaphore
- **New API Endpoints**:
  - `!cd ping` - Ping Semaphore server to check connectivity
  - `!cd info` - Get Semaphore server information
  - `!cd aliases` - List all configured command aliases
- **TUI Aliases Screen**: Interactive alias management
  - Add new aliases with validation
  - Delete existing aliases
  - View all configured aliases
  - Accessible via `x` hotkey in main menu

### Fixed
- **CRITICAL**: Fixed TUI crash when OIDC authentication is detected
  - OIDCAuthScreen now uses TextArea instead of markup links to avoid MarkupError with URLs containing special characters
  - URLs like `https://chat.example.org/_matrix/client/v3/login/sso/redirect/oidc?redirectUrl=http://localhost:8080/callback` no longer cause crashes
  - Fixes issue where app would crash with MarkupError during OIDC authentication flow in TUI mode
- **CRITICAL**: Fixed OIDC authentication hanging when running with TUI (default interactive mode)
  - Issue #59 recurrence: The code was trying to push OIDC screen to TUI before TUI was started
  - Refactored `run_tui_with_bot` to start TUI first, then perform login within TUI context
  - Login now happens in TUI's `on_mount` lifecycle method after TUI is fully running
  - This fixes the hang when running `chatrixcd -vvv` or any interactive terminal mode with OIDC authentication
- **CRITICAL**: Fixed OIDC authentication hanging when attempting to parse identity providers from server response
  - The code was attempting to re-read an already consumed aiohttp response body, causing the authentication flow to hang
  - Now makes a fresh HTTP request to `/_matrix/client/v3/login` to obtain identity provider information
  - Fixes authentication with OIDC-enabled Matrix servers (e.g., chat.privacyinternational.org)
  - Falls back gracefully to generic SSO URL if identity provider fetch fails

### Added
- TUI support for `-s`/`--show-config` flag
  - When `-s` is used without `-R` (redact) or `-v` (verbose) flags, configuration is now displayed in a TUI window
  - Provides a more user-friendly interface for viewing configuration
  - Press 'q' or ESC to exit the configuration viewer
- Comprehensive error handling to prevent stacktraces in production
  - Unhandled exceptions in TUI and main application are now caught and displayed as user-friendly messages
  - Stacktraces are only shown when running with `-v`, `-vv`, or `-vvv` flags (debug mode)
  - Users are prompted to run with `-v` or `-vv` for more details when errors occur

### Improved
- Added verbose debug logging throughout OIDC authentication flow for better diagnostics
  - Logs redirect URL, SSO URL construction, identity provider selection
  - Logs callback invocation and token retrieval steps
  - Helps diagnose authentication issues when running with `-vv` or `-vvv` flags

### Changed
- **BREAKING**: Dropped support for Python 3.9, 3.10, and 3.11 - minimum required version is now Python 3.12
- Updated to support Python 3.12, 3.13, and 3.14
- Updated all documentation to reflect new Python version requirements
- Updated GitHub Actions CI/CD workflow to test Python 3.12, 3.13, and 3.14
- Updated ARCHITECTURE.md to reflect new OIDC identity provider parsing approach

## [2025.10.14.1.0.0] - 2025-10-14

### Changed
- **BREAKING**: Removed token-based authentication method
- **BREAKING**: Removed OAuth2 client credentials OIDC flow
- **BREAKING**: Dropped Python 3.8 support - minimum required version is now Python 3.9
- Refactored authentication to use native Matrix SDK methods exclusively
- OIDC authentication now uses Matrix SSO/token-based login flow
- Simplified authentication configuration (removed `oidc_issuer`, `oidc_client_id`, `oidc_client_secret`)
- Updated OIDC configuration to use `oidc_redirect_url` instead

### Improved
- Authentication now uses matrix-nio's native login methods
- Better encryption support with proper E2E key handling
- More reliable OIDC/SSO authentication following Matrix specification
- Clearer authentication flow with user prompts for OIDC login
- **OIDC authentication now properly queries server for identity providers**
- **Support for multiple identity providers with user selection**
- **Generates correct provider-specific SSO URLs when available**

### Fixed
- Fixed encrypted session failures in 1-1 rooms with OIDC authentication
- Improved encryption key management and session handling
- **Corrected OIDC/SSO implementation to properly parse server login flow response**
- **Fixed configuration validation to match current OIDC implementation** - removed legacy checks for `oidc_issuer`, `oidc_client_id`, and `oidc_client_secret` which are no longer required
- **Fixed version management** - `setup.py` and `pyproject.toml` now read version dynamically from `chatrixcd/__init__.py` instead of hardcoding

## [2025.10.12.0.0.1] - 2025-10-12

### Added

#### Interactive TUI (Text User Interface)
- **Interactive Mode**: New Text User Interface (TUI) when running ChatrixCD interactively
  - Menu-driven interface with brand colors (ChatrixCD green: #4A9B7F)
  - Mouse support for easy navigation
  - Works without color support when `-C` flag is not used
- **Real-Time Task Monitoring**: 
  - Active tasks widget on home screen showing running Semaphore tasks
  - Live status updates every 5 seconds
  - Color-coded status indicators (running, success, error, stopped)
- **TUI Menu Options**:
  - **STATUS**: View bot status (Matrix/Semaphore connections, uptime, metrics including messages processed, errors, warnings)
  - **ADMINS**: View admin users configured for the bot
  - **ROOMS**: View all rooms the bot has joined
  - **SESSIONS**: Comprehensive encryption session management
    - View active encryption sessions with verification status
    - **Full interactive emoji verification using Matrix SDK (SAS protocol)**
      - Select unverified devices from list
      - Initiate SAS verification with chosen device
      - Compare 7 cryptographically-secure emojis
      - Confirm or reject verification interactively
      - Automatic MAC exchange and verification
      - Compatible with all Matrix clients (Element, FluffyChat, etc.)
    - QR code device verification
    - Device fingerprint display for manual verification
    - Olm session reset instructions
  - **SAY**: Send messages to rooms from the bot
  - **LOG**: View bot logs in real-time within the TUI
  - **SET**: Interactive configuration editing
    - Edit command prefix, greetings, and messages
    - Apply changes to runtime only or save to config.json
    - Type validation and change preview
    - Pending changes tracking
  - **SHOW**: View current configuration with redacted credentials
  - **QUIT**: Gracefully shutdown the bot
- **New Command-Line Flags**:
  - `-L, --log-only`: Run in classic log-only mode (no TUI, backward compatible behavior)
  - TUI automatically disabled when running in daemon mode (`-D`) or non-interactive terminal
- **Color Support**: TUI uses brand colors when `-C` flag is used, but remains fully functional without color support
- **Dependencies**: 
  - Added `textual>=0.47.0` for TUI implementation
  - Added `qrcode>=7.4.2` for QR code generation in device verification

### Fixed
- **Encrypted Room Support**: Fixed issue where bot would not respond to commands in encrypted rooms. The bot now properly handles successfully decrypted Megolm events and processes them as normal messages
- **Bot Message Processing**: Fixed issue where bot would process old messages on reconnect or startup. The bot now ignores messages that were sent before it started, preventing execution of stale commands and tasks that may have already been processed
- **Redaction Feature**: Fixed redaction feature leaving some information un-redacted when using `-R` flag
  - User IDs with URL-encoded characters (e.g., `@chrisw=40privacyinternational.org`) are now properly redacted
  - Cryptographic sender keys in JSON context are now redacted with `[SENDER_KEY_REDACTED]` marker
  - Session IDs in various formats (including with trailing dots) are now properly redacted
  - Device IDs in JSON string context (e.g., `'device_id': 'XYEZMPLXBC'`) are now properly redacted

#### Matrix SDK Integration
- **Key Verification Event Callbacks**: Added support for handling key verification protocol events
  - `KeyVerificationStart`: Handles incoming verification requests
  - `KeyVerificationCancel`: Handles verification cancellations
  - `KeyVerificationKey`: Handles key exchange during verification
  - `KeyVerificationMac`: Handles MAC verification completion
  - Full SAS (Short Authentication String) protocol support

#### Privacy and Security Features
- **Sensitive Information Redaction**: New `-R` / `--redact` command-line flag to automatically redact sensitive information from logs
  - Redacts Matrix room IDs (e.g., `!room:server.com` → `![ROOM_ID]:server.com`)
  - Redacts Matrix user IDs (e.g., `@user:matrix.org` → `@[USER]:matrix.org`)
  - Redacts IPv4 addresses (e.g., `192.168.1.100` → `192.168.xxx.xxx`)
  - Redacts IPv6 addresses (e.g., `2001:db8::1` → `2001:db8:[IPV6_REDACTED]`)
  - Redacts hostnames and domains (e.g., `internal.example.com` → `internal.[DOMAIN].com`)
  - Redacts authentication tokens and API keys
  - Redacts passwords in URLs and parameters
  - Redacts session IDs, device IDs, and host keys
  - Works with all verbosity levels (`-v`, `-vv`, `-vvv`)
  - Works with `--show-config` flag to redact identifiers in configuration output
  - When combined with `-C` (color), redacted content is highlighted in pink for easy identification
  - New `chatrixcd.redactor` module with `SensitiveInfoRedactor` and `RedactingFilter` classes
  - Comprehensive test coverage in `tests/test_redactor.py`

#### Dependencies
- **colorlog**: Added `colorlog>=6.7.0` to requirements.txt for colored logging support
  - Ensures `-C` / `--color` flag works properly out of the box
  - Provides colored console output with customizable log level colors
  - Pink highlighting for redacted content when used with `-R` flag

### Changed

#### Documentation
- **Bug Report Template**: Updated `.github/ISSUE_TEMPLATE/bug_report.yml` to recommend using `-R` flag for privacy
- **README.md**: Added `-R` flag documentation and privacy notes
- **INSTALL.md**: Added security best practices for log redaction
- **SUPPORT.md**: Updated debugging section with redaction examples
- **CONTRIBUTING.md**: Added privacy recommendations for bug reports

## [2025.10.8] - 2025-10-10

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
- **Branding and Visual Identity**: Comprehensive branding guidelines and styling with SVG logos
  - Added `BRANDING.md` with complete brand guidelines and color palette
  - Created `assets/` directory with SVG logo files (horizontal, icon, stacked, social, favicon)
  - All logos in scalable SVG format for perfect quality at any size
  - Added custom CSS for GitHub Pages with ChatrixCD brand colors (#4A9B7F green)
  - Updated README.md with centered header, logo display, badges, and branding elements
  - Updated documentation index page with logo and consistent branding
  - Added README files in asset directories with logo specifications and usage instructions
  - Brand colors: ChatrixCD Green (#4A9B7F), Dark Background (#2D3238), White (#FFFFFF)
  - Logos integrated and visible in README and documentation
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

---

## Version History









- **2025.10.18.3.1.0** (2025-10-18)
- **2025.10.17.3.0.0** (2025-10-17)
- **2025.10.17.2.0.0** (2025-10-17)
- **2025.10.14.1.0.0** (2025-10-14)
- **2025.10.12.0.0.1** (2025-10-12)
- **2025.10.8** (2025-10-10)
- **2025.10.7** (2025-10-09)
- **2025.10.6** (2025-10-09)
- **0.1.0** (2024-01-08) - Initial release with OIDC support
