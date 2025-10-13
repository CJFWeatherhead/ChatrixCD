# Architecture Documentation

This document describes the architecture and design of ChatrixCD.

## Development Notice

**Important:** Large portions of this project were developed with assistance from AI/LLM tools (GitHub Copilot, Large Language Models). While all code has been reviewed, tested, and validated by human developers, the architecture and implementation reflect AI-assisted development practices.

## Overview

ChatrixCD is a Matrix bot that bridges Matrix chat with Semaphore UI for CI/CD automation. It's built using asynchronous Python with support for end-to-end encryption and modern authentication methods including OIDC.

## Matrix Protocol Compliance

ChatrixCD implements Matrix protocol features using the [matrix-nio](https://github.com/poljar/matrix-nio) client library, which provides:

- **Matrix Client-Server API**: Full compliance with Matrix spec for messaging, rooms, and events
- **End-to-End Encryption (E2EE)**: Implements Olm and Megolm protocols as specified in Matrix spec
- **SSO/OIDC Authentication**: Uses Matrix SSO flow (MSC2858) for OIDC authentication
- **Device Verification**: Supports SAS (Short Authentication String) emoji verification
- **Key Management**: Automatic key sharing and device cross-signing as per Matrix spec

**Matrix Specification References:**
- [Matrix Client-Server API](https://spec.matrix.org/latest/client-server-api/)
- [End-to-End Encryption](https://spec.matrix.org/latest/client-server-api/#end-to-end-encryption)
- [SSO Login Flow](https://spec.matrix.org/latest/client-server-api/#sso-client-login)
- [MSC2858: Multiple SSO Identity Providers](https://github.com/matrix-org/matrix-spec-proposals/pull/2858)

## System Architecture

```
┌─────────────────┐
│  Matrix Server  │
│   (with OIDC)   │
└────────┬────────┘
         │ Matrix Protocol
         │ (E2E Encrypted)
         │
    ┌────▼─────┐
    │          │
    │ ChatrixCD│
    │   Bot    │
    │          │
    └────┬─────┘
         │ REST API
         │
┌────────▼──────────┐
│  Semaphore UI     │
│  (Task Runner)    │
└───────────────────┘
```

## Components

### 1. Main Entry Point (`main.py`)

**Purpose**: Application bootstrap and lifecycle management

**Responsibilities**:
- Initialize logging
- Load configuration
- Create bot instance
- Determine run mode (TUI, log-only, or daemon)
- Handle graceful shutdown

**Key Functions**:
- `main()`: Entry point that orchestrates startup
- `setup_logging()`: Configures logging to file and stdout
- `run_tui_with_bot()`: Runs the bot with TUI interface

**Run Modes**:
- **Interactive TUI Mode**: Default when running in an interactive terminal without `-L` or `-D` flags
- **Log-Only Mode**: Classic behavior, activated with `-L` flag
- **Daemon Mode**: Background process, activated with `-D` flag

### 2. Configuration Manager (`config.py`)

**Purpose**: Centralized configuration management

**Features**:
- JSON file support
- Environment variable fallback
- Hierarchical key access with dot notation
- Separate getters for Matrix, Semaphore, and bot configs

**Configuration Sources** (in order of precedence):
1. JSON configuration file
2. Environment variables
3. Default values

### 3. Authentication Handler (`auth.py`)

**Purpose**: Configuration and validation for Matrix authentication

**Supported Methods**:

#### Password Authentication
- Traditional Matrix username/password login
- Handled natively by matrix-nio's `AsyncClient.login(password=...)`
- Simplest and most common method
- Works with standard Matrix homeservers

#### OIDC/SSO Authentication
- Matrix SSO login using OIDC providers
- Interactive browser-based authentication flow
- Uses matrix-nio's `AsyncClient.login(token=...)`
- Ideal for enterprise Matrix deployments with centralized authentication

**OIDC Authentication Flow**:
```
1. Query server for available login flows via AsyncClient.login_info()
2. Parse response to extract SSO flow and identity providers
3. If multiple identity providers, present options to user
4. Generate appropriate SSO redirect URL:
   - Single provider: /_matrix/client/v3/login/sso/redirect/{provider_id}?redirectUrl={url}
   - Generic/No providers: /_matrix/client/v3/login/sso/redirect?redirectUrl={url}
5. User opens URL in browser and authenticates with OIDC provider
6. User receives callback URL with loginToken parameter
7. User provides token to bot
8. Bot completes login using AsyncClient.login(token=loginToken)
```

**Implementation Notes**:
- All authentication uses native matrix-nio methods
- Server response contains detailed flow information including identity providers
- Implementation parses transport_response to access identity provider details
- Supports multiple identity providers with user selection
- No custom OAuth2 client implementation needed
- Encryption store is automatically loaded by matrix-nio after successful login

### 4. Bot Core (`bot.py`)

**Purpose**: Main bot logic and Matrix client management

**Key Components**:

- **AsyncClient Integration**: Uses matrix-nio for Matrix protocol
- **E2E Encryption**: Automatic encryption key management via store
- **Event Handling**: Callbacks for messages, invites, and encrypted messages
- **Auto-Join**: Automatically joins rooms when invited

**Event Callbacks**:
- `message_callback()`: Process incoming messages (decrypted messages)
- `invite_callback()`: Handle room invitations
- `megolm_event_callback()`: Handle encrypted messages and request keys when needed

**Authentication Flow**:
```python
if auth_type == 'password':
    # Native password login
    response = await client.login(password=password, device_name=device_name)
    await setup_encryption()
    
elif auth_type == 'oidc':
    # Interactive SSO login
    login_info = await client.login_info()
    # Display SSO URL to user
    token = input("Paste loginToken: ")
    response = await client.login(token=token, device_name=device_name)
    await setup_encryption()
```

### 5. Command Handler (`commands.py`)

**Purpose**: Parse and execute bot commands

**Command Flow**:
```
1. Check message starts with command prefix
2. Verify room is allowed (if configured)
3. Parse command and arguments
4. Route to appropriate handler
5. Execute command
6. Send response to room
```

**Available Commands**:
- `help`: Show command list
- `projects`: List Semaphore projects
- `templates <project_id>`: List templates
- `run <project_id> <template_id>`: Start task
- `status <task_id>`: Check task status
- `stop <task_id>`: Stop running task
- `logs <task_id>`: Get task output

**Task Monitoring**:
- Tracks active tasks in memory
- Polls Semaphore every 10 seconds
- Sends status updates to room
- Removes completed/failed tasks

### 6. Semaphore Client (`semaphore.py`)

**Purpose**: REST API client for Semaphore UI

**Features**:
- Async HTTP client using aiohttp
- Bearer token authentication
- Full CRUD operations for tasks

**API Methods**:
- `get_projects()`: List all projects
- `get_project_templates(project_id)`: List templates
- `start_task(project_id, template_id)`: Start new task
- `get_task_status(project_id, task_id)`: Get task info
- `get_task_output(project_id, task_id)`: Get logs
- `stop_task(project_id, task_id)`: Stop running task

**Connection Management**:
- Lazy session creation
- Automatic session cleanup
- Persistent authentication header

### 7. Text User Interface (`tui.py`)

**Purpose**: Interactive terminal interface for bot management

**Features**:
- Menu-driven interface with brand colors
- Mouse support for navigation
- Real-time status monitoring
- Interactive room messaging
- Log viewing
- Configuration display

**Key Components**:
- **ChatrixTUI**: Main TUI application class
- **BotStatusWidget**: Real-time status display widget
- **Screen Classes**: Individual screens for each menu option
  - `AdminsScreen`: Display admin users
  - `RoomsScreen`: Display joined rooms
  - `SessionsScreen`: Manage encryption sessions
  - `SayScreen`: Send messages to rooms
  - `LogScreen`: View bot logs
  - `SetScreen`: Change operational variables
  - `ShowScreen`: Display configuration

**Integration**:
- Runs alongside the bot using asyncio
- Shares bot instance for direct control
- Updates in real-time based on bot state

**Color Support**:
- Uses brand colors when `-C` flag is enabled
- Fully functional without color support
- Brand green (#4A9B7F) for headers and primary elements
- Dark background (#2D3238) for footer

## Data Flow

### Starting a Task

```
User sends: !cd run 1 5
           ↓
CommandHandler.handle_message()
           ↓
CommandHandler.run_task()
           ↓
SemaphoreClient.start_task(1, 5)
           ↓ HTTP POST
Semaphore UI creates task
           ↓ Returns task ID
CommandHandler stores task in active_tasks
           ↓
Bot sends: "✅ Task 123 started"
           ↓
CommandHandler.monitor_task() background loop
           ↓ Polls every 10s
SemaphoreClient.get_task_status()
           ↓
Bot sends status updates:
  "🔄 Task 123 is running..."
  "✅ Task 123 completed!"
```

### Authentication Flow (Password)

```
Bot starts
    ↓
Config loads Matrix settings
    ↓
AsyncClient.login(password=password)
    ↓
Matrix server validates credentials
    ↓
Receive access_token and device_id
    ↓
Load encryption store
    ↓
Upload/query encryption keys
    ↓
Bot ready to receive messages
```

### Authentication Flow (OIDC/SSO)

```
Bot starts
    ↓
AsyncClient.login_info() - Query server for login flows
    ↓
Parse response for m.login.sso flow and identity_providers
    ↓
If multiple providers, user selects one
    ↓
Generate SSO redirect URL:
  - With provider: {homeserver}/_matrix/client/v3/login/sso/redirect/{provider_id}?redirectUrl={url}
  - Generic: {homeserver}/_matrix/client/v3/login/sso/redirect?redirectUrl={url}
    ↓
Display SSO URL to user
    ↓
User opens URL in browser
    ↓
User authenticates with OIDC provider
    ↓
User receives callback with loginToken
    ↓
User provides token to bot
    ↓
AsyncClient.login(token=loginToken)
    ↓
Matrix server validates token
    ↓
Receive access_token and device_id
    ↓
Load encryption store
    ↓
Upload/query encryption keys
    ↓
Bot ready to receive messages
```

## Security Considerations

### Encryption

- **E2E Encryption**: Full support via matrix-nio
- **Key Storage**: Encrypted keys stored in configurable directory
- **Device Verification**: Supports device verification workflows
- **Automatic Key Requests**: When the bot receives an encrypted message it cannot decrypt (MegolmEvent), it automatically requests the encryption key from other devices in the room. Once the key is received, the message will be decrypted on the next sync and processed normally.

### Authentication

- **Password Security**: 
  - Passwords never logged
  - Stored only in configuration file
  - Use strong, unique passwords
  - Consider using environment variables for sensitive data

- **OIDC/SSO Security**:
  - Uses native Matrix SSO/OIDC flow
  - Server provides identity provider details
  - Token-based authentication
  - No credentials stored after initial login
  - Supports standard OIDC providers (Keycloak, Authentik, etc.)
  - Multi-provider support with user selection

### Access Control

- **Room Allowlist**: Restrict bot to specific rooms
- **Admin Users**: Limit certain commands to admins
- **No privilege escalation**: Bot has only its granted permissions

### Secrets Management

- **Configuration**: Supports external secret management
- **Environment Variables**: Recommended for production
- **File Permissions**: Config files should be readable only by bot user

## Deployment Models

### Development

```bash
python -m chatrixcd.main
```

- Direct Python execution
- Logs to console and file
- Configuration from local files

### Production - Systemd

```
systemd service → Python virtualenv → Bot process
```

- Automatic restart on failure
- Proper user isolation
- Security hardening (NoNewPrivileges, PrivateTmp)
- Logs to systemd journal

### Production - Docker

```
Docker container → Persistent volumes for store/
```

- Isolated environment
- Easy updates via image rebuilds
- Volume mounts for state preservation
- Environment-based configuration

### Production - Docker Compose

```
docker-compose.yml → Orchestration
```

- Environment file management
- Service dependencies
- Log aggregation
- Easy scaling

## Performance Characteristics

### Resource Usage

- **Memory**: ~50-100 MB baseline
- **CPU**: Minimal (event-driven)
- **Network**: 
  - Matrix: Persistent connection (sync loop)
  - Semaphore: Polling every 10s per active task

### Scalability

- **Concurrent Tasks**: Limited only by memory
- **Rooms**: Can monitor unlimited rooms
- **Commands**: Async processing, no blocking

### Bottlenecks

- Matrix sync latency (~30s typical)
- Semaphore API rate limits
- Task polling frequency (configurable)

## Error Handling

### Retry Logic

- **Matrix Sync**: Automatic retry via matrix-nio
- **Semaphore API**: No automatic retry (returns error)
- **Task Monitoring**: Continues on transient failures

### Error Recovery

- **Connection Loss**: Bot reconnects automatically
- **Invalid Commands**: Friendly error messages to user
- **API Failures**: Logged and reported to user

### Logging

- **Levels**: INFO for normal operation, ERROR for failures
- **Destinations**: 
  - stdout (for Docker/systemd)
  - chatrixcd.log file
- **Format**: Timestamp, logger name, level, message

## Extension Points

### Adding New Commands

1. Add handler method in `CommandHandler`
2. Add routing in `handle_message()`
3. Update help text

### Supporting Other CI/CD Systems

1. Create new client class (like `semaphore.py`)
2. Implement required API methods
3. Update `CommandHandler` to use new client

### Custom Authentication

1. Add new auth type in `MatrixAuth`
2. Implement token acquisition method
3. Update configuration schema

## Testing Strategy

### Unit Tests

- Configuration loading
- Command parsing
- Authentication token handling

### Integration Tests (Future)

- Matrix client authentication
- Semaphore API calls
- End-to-end command flow

### Manual Testing

- Actual Matrix rooms
- Real Semaphore instance
- Various authentication methods

## Dependencies

### Core

- **matrix-nio**: Matrix protocol implementation
- **aiohttp**: Async HTTP client

### Platform

- **Python 3.9+**: Async/await support and modern syntax features
- **Linux/macOS/Windows**: Cross-platform

## Future Enhancements

### Planned Features

- [ ] Interactive task parameter input
- [ ] Task scheduling via cron syntax
- [ ] Multi-tenant support (multiple Semaphore instances)
- [ ] Webhook support for push notifications
- [ ] Rich message formatting for task output
- [ ] Task history and analytics
- [ ] Admin dashboard

### Potential Improvements

- [ ] GraphQL support for Matrix (when available)
- [ ] Reduce task polling overhead
- [ ] Cache Semaphore project/template lists
- [ ] Support for task dependencies
- [ ] Parallel task execution

## Maintenance

### Monitoring

- Check bot process is running
- Review logs for errors
- Monitor store directory size
- Track task completion rates

### Updates

- Review matrix-nio changelogs
- Update dependencies regularly
- Test authentication after updates
- Backup store directory before upgrades

### Backup

**Critical Data**:
- `store/` directory (encryption keys)
- Configuration files
- Logs (for audit trail)

**Not Critical**:
- Task tracking state (in-memory only)
- Temporary files
