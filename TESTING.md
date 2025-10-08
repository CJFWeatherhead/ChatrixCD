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

### Overall Coverage: 16%

| Module | Coverage | Lines | Tested | Description |
|--------|----------|-------|--------|-------------|
| `__init__.py` | 100% | 1 | 1 | Package initialization |
| `config.py` | 89% | 27 | 24 | Configuration management |
| `auth.py` | 38% | 95 | 36 | Authentication (password, token, OIDC) |
| `semaphore.py` | 23% | 94 | 22 | Semaphore API client |
| `bot.py` | 0% | 89 | 0 | Matrix bot core (requires integration) |
| `commands.py` | 0% | 185 | 0 | Command handlers (requires integration) |
| `main.py` | 0% | 22 | 0 | Entry point (tested via integration) |

### Test Suite Composition

- **Total Tests**: 18
- **Configuration Tests**: 4
- **Authentication Tests**: 10
- **Semaphore Client Tests**: 4

## Test Categories

### Unit Tests (Current)

#### Configuration Module (`tests/test_config.py`)
- ✅ Default values loading
- ✅ Environment variable configuration
- ✅ YAML file configuration
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
- ✅ Session creation
- ✅ Session cleanup

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

### Short-term (Current)
- ✅ Config: 89%
- ✅ Auth: 38%
- ✅ Semaphore: 23%

### Medium-term (Next Release)
- ⏳ Config: 95%
- ⏳ Auth: 80% (full OIDC flow testing)
- ⏳ Semaphore: 70% (all API methods)
- ⏳ Bot: 40% (basic unit tests)

### Long-term (Future)
- ⏳ Overall: 80%+
- ⏳ Integration tests for full workflows
- ⏳ End-to-end testing with test Matrix server

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
