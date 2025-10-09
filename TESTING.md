# Testing Guide

This document describes the test suite and coverage for ChatrixCD.

## Running Tests

### Basic Test Run

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

### Test Coverage

```bash
# Run tests with coverage report
pytest tests/ --cov=chatrixcd --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=chatrixcd --cov-report=html
# Open htmlcov/index.html in a browser
```

## Test Coverage Summary

### Overall Coverage: 64%

| Module | Coverage | Lines | Tested | Description |
|--------|----------|-------|--------|-------------|
| `__init__.py` | 100% | 1 | 1 | Package initialization |
| `config.py` | 87% | 142 | 123 | Configuration management |
| `auth.py` | 38% | 95 | 36 | Authentication (password, token, OIDC) |
| `semaphore.py` | 87% | 94 | 82 | Semaphore API client |
| `bot.py` | 72% | 143 | 103 | Matrix bot core and lifecycle |
| `commands.py` | 84% | 185 | 155 | Command handlers |
| `main.py` | 0% | 123 | 0 | Entry point (requires integration tests) |

### Test Suite Composition

- **Total Tests**: 112
- **Configuration Tests**: 18
- **Authentication Tests**: 10
- **Bot Tests**: 17
- **CLI Tests**: 10
- **Command Handler Tests**: 38
- **Semaphore Client Tests**: 19

## Test Categories

### Unit Tests (Current)

#### Configuration Module (`tests/test_config.py`)
- ✅ Default values loading
- ✅ Environment variable configuration
- ✅ JSON file configuration
- ✅ Fallback and default value handling

#### Authentication Module (`tests/test_auth.py`)
- ✅ Password authentication initialization
- ✅ Token authentication initialization
- ✅ OIDC authentication initialization
- ✅ Access token retrieval for password auth
- ✅ Access token retrieval for token auth
- ✅ Missing token handling
- ✅ Unknown auth type handling
- ✅ OIDC missing configuration
- ✅ Token refresh without refresh token
- ✅ Token refresh with wrong auth type

#### Semaphore Client Module (`tests/test_semaphore.py`)
- ✅ Client initialization
- ✅ URL trailing slash handling
- ✅ Session creation and cleanup
- ✅ Get projects (success, failure, exception)
- ✅ Get project templates (success, failure)
- ✅ Start task (success, failure, with options)
- ✅ Get task status (success, failure)
- ✅ Get task output/logs (success, failure)
- ✅ Stop task (success, failure, exception)

#### Command Handler Module (`tests/test_commands.py`)
- ✅ Handler initialization
- ✅ Room permission checks (allowed_rooms)
- ✅ Admin permission checks (admin_users)
- ✅ Message filtering (command prefix, non-commands)
- ✅ Help command
- ✅ List projects (success, empty)
- ✅ List templates (success, empty, invalid args)
- ✅ Run task (success, failure, validation)
- ✅ Check task status
- ✅ Stop task
- ✅ Get task logs (including truncation)
- ✅ Unknown command handling

#### Bot Module (`tests/test_bot.py`)
- ✅ Callback registration
- ✅ Message filtering (own messages)
- ✅ Decryption failure handling
- ✅ Login validation (user_id checks)
- ✅ Encryption store loading
- ✅ Startup messages (enabled/disabled)
- ✅ Shutdown messages (enabled/disabled)
- ✅ Room invite handling
- ✅ Message sending (plain text, HTML formatted)

### Integration Tests (Future)

The following areas require integration testing with live services:

#### Bot Core (`bot.py`)
- Matrix client connection
- Room joining and sync
- Message sending and receiving
- Encryption handling
- Event callbacks

#### Command Handler (`commands.py`)
- Command parsing
- Project listing
- Template listing
- Task execution
- Task monitoring
- Status reporting
- Error handling

#### Main Entry Point (`main.py`)
- Application startup
- Configuration loading
- Signal handling
- Graceful shutdown

## Testing Best Practices

### Running Tests Before Commits

```bash
# Quick test
pytest tests/

# Full test with coverage
pytest tests/ --cov=chatrixcd --cov-report=term-missing
```

### Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach when possible)
2. **Test edge cases**: Empty inputs, None values, errors
3. **Mock external dependencies**: Matrix servers, Semaphore API
4. **Use descriptive test names**: `test_<what>_<condition>_<expected>`
5. **Keep tests isolated**: Each test should be independent

### Test File Organization

```
tests/
├── __init__.py
├── test_config.py       # Configuration tests
├── test_auth.py         # Authentication tests
├── test_semaphore.py    # Semaphore client tests
└── test_bot.py          # (Future) Bot integration tests
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)

See `.github/workflows/test.yml` for CI configuration.

## Coverage Goals

### Current Status
- ✅ Config: 87%
- ⏳ Auth: 38% (needs OIDC integration tests)
- ✅ Semaphore: 87% (all API methods tested)
- ✅ Bot: 72% (core functionality tested)
- ✅ Commands: 84% (comprehensive command tests)
- ✅ Overall: 64%

### Next Release Goals
- ⏳ Auth: 70%+ (full OIDC flow testing with mock server)
- ⏳ Bot: 80%+ (additional edge cases)
- ⏳ Overall: 70%+
- ⏳ Integration tests for task monitoring workflows

### Long-term (Future)
- ⏳ Overall: 80%+
- ⏳ Full integration tests with Matrix server
- ⏳ End-to-end testing with Semaphore instance
- ⏳ Performance and stress testing

## Known Limitations

1. **Async Mocking Complexity**: Some async tests with aiohttp are simplified to avoid complex mocking issues
2. **Matrix Server Required**: Bot and command tests require a test Matrix server
3. **Semaphore Server Required**: Full Semaphore tests need a test Semaphore instance
4. **No End-to-End Tests**: Currently no full workflow tests from command to task completion

## Contributing Tests

When contributing tests:

1. Ensure all tests pass: `pytest tests/`
2. Check coverage doesn't decrease: `pytest tests/ --cov=chatrixcd`
3. Follow existing test patterns
4. Document complex test scenarios
5. Use meaningful assertions with clear error messages

## Test Development Tools

Recommended tools for test development:

```bash
# Install development tools
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::TestMatrixAuth::test_init_password_auth -v

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [INSTALL.md](INSTALL.md) - Installation guide
- [README.md](README.md) - Project overview
