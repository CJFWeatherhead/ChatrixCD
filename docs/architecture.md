---
layout: default
title: Architecture
nav_order: 5
---

# Architecture Overview

ChatrixCD is built with a modular, asynchronous architecture for reliable Matrix bot operation.

## System Architecture

```
┌─────────────────┐
│  Matrix Client  │
│    (nio)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│   Bot Core      │◄────►│   Commands   │
│   (bot.py)      │      │  (commands.py)│
└────────┬────────┘      └──────┬───────┘
         │                       │
         ▼                       ▼
┌─────────────────┐      ┌──────────────┐
│   Auth Handler  │      │  Semaphore   │
│   (auth.py)     │      │   Client     │
└─────────────────┘      │(semaphore.py)│
                         └──────────────┘
         ▲
         │
┌─────────────────┐
│  Configuration  │
│   (config.py)   │
└─────────────────┘
```

## Core Components

### Main Entry Point (`main.py`)

- Application lifecycle management
- Signal handling (SIGINT, SIGTERM)
- Graceful shutdown
- Error recovery

### Configuration (`config.py`)

- JSON configuration file parsing
- Environment variable handling
- Configuration validation
- Default value management

### Authentication (`auth.py`)

- Matrix authentication handling
- Support for password authentication
- Support for token authentication
- OIDC/OAuth2 authentication
- Token refresh and management

### Bot Core (`bot.py`)

- Matrix client initialization
- Room management and sync
- Event handling and dispatch
- Message sending
- E2E encryption support
- Callback registration

### Command Handler (`commands.py`)

- Command parsing and routing
- Project listing
- Template management
- Task execution
- Status monitoring
- Error handling and user feedback

### Semaphore Client (`semaphore.py`)

- REST API client for Semaphore UI
- Async HTTP requests
- Project and template queries
- Task lifecycle management
- Log retrieval

## Data Flow

### Command Execution Flow

1. User sends message to Matrix room
2. Bot receives message event
3. Command parser extracts command and arguments
4. Command handler validates and executes
5. Semaphore API call made if needed
6. Response sent back to Matrix room

### Task Monitoring Flow

1. Task started via `!cd run` command
2. Task ID stored for monitoring
3. Periodic status checks to Semaphore API
4. Status updates sent to Matrix room
5. Monitoring stops on task completion/failure

## Technology Stack

### Core Libraries

- **matrix-nio**: Matrix protocol client with E2E encryption
- **aiohttp**: Async HTTP client for API requests
- **authlib**: OAuth2/OIDC authentication

### Python Version Support

- Python 3.8+
- Async/await throughout
- Type hints for better IDE support

## Security Architecture

### Credential Management

- No credentials in logs
- Environment variable support
- Secure token storage
- In-memory only sensitive data

### Encryption

- E2E encryption via matrix-nio
- Encryption keys stored in `store/` directory
- Device verification support
- Key backup and recovery

### Access Control

- Room-based access control
- User permission checking
- Command authorization
- Rate limiting (future)

## Async Architecture

### Event Loop

All I/O operations are asynchronous:

- Matrix client sync
- HTTP API requests
- Message handling
- Task monitoring

### Concurrency

- Single event loop
- Concurrent task monitoring
- Non-blocking I/O operations
- Proper resource cleanup

## Storage

### Encryption Store

- Location: `store/` directory (configurable)
- Contents: Encryption keys, device IDs
- Format: SQLite database (managed by matrix-nio)
- Security: Restricted file permissions

### No Persistent State

- No database required
- Stateless command handling
- Task IDs managed by Semaphore
- Configuration from files/environment

## Error Handling

### Graceful Degradation

- Connection retry logic
- Timeout handling
- Partial failure recovery
- User-friendly error messages

### Logging

- Structured logging
- Multiple log levels
- Security-conscious (no secrets)
- Configurable output

## Extensibility

### Plugin Architecture (Future)

- Command plugins
- Custom task handlers
- Event processors
- Integration modules

### Configuration Extension

- Custom command prefixes
- Multiple Semaphore instances (future)
- Room-specific settings (future)

## Performance Considerations

### Resource Usage

- Low memory footprint
- Efficient async I/O
- Minimal CPU usage
- Scalable to many rooms

### Optimization

- Connection pooling
- Request batching
- Efficient sync
- Minimal polling

## Deployment Architecture

### Containerized Deployment

- Docker support (Debian and Alpine)
- Volume mounts for config and store
- Health checks
- Auto-restart policies

### Native Deployment

- systemd service (Linux)
- OpenRC service (Alpine)
- Process supervision
- Log management

## Related Documentation

- [Configuration Guide](configuration.html)
- [Contributing Guidelines](contributing.html)
- [Security Policy](security.html)
