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

### Overall Coverage: 40%

| Module | Coverage | Lines | Tested | Description |
|--------|----------|-------|--------|-------------|
| `__init__.py` | 100% | 1 | 1 | Package initialization |
| `config.py` | 71% | 200 | 142 | Configuration management |
| `auth.py` | 100% | 22 | 22 | Authentication (password, OIDC) |
| `semaphore.py` | 68% | 143 | 97 | Semaphore API client |
| `bot.py` | 52% | 537 | 281 | Matrix bot core and lifecycle |
| `commands.py` | 55% | 704 | 384 | Command handlers |
| `main.py` | 23% | 294 | 67 | Entry point (E2E tests added!) |
| `verification.py` | 56% | 235 | 132 | Device verification |
| `messages.py` | 69% | 88 | 61 | Message templates |
| `redactor.py` | 93% | 69 | 64 | Sensitive information redaction |
| `aliases.py` | 71% | 111 | 79 | Command aliases |

### Test Suite Composition

- **Total Tests**: 388
- **Configuration Tests**: 18
- **Authentication Tests**: 10
- **Bot Tests**: 17
- **CLI Tests**: 10
- **Command Handler Tests**: 38
- **Semaphore Client Tests**: 19
- **Verification Tests**: 19
- **Verification E2E Tests**: 20
- **Message Tests**: 10
- **Aliases Tests**: 14
- **TUI Tests**: 101 (⬆️ increased from 40!)
  - **Unit Tests**: 40 (component creation and imports)
  - **Pilot Core Tests**: 44 (main app, screens, widgets)
  - **Pilot Interactive Tests**: 17 (workflows, navigation, error handling)
- **Redactor Tests**: 9
- **Workflow Tests**: 104
- **Main Entry Point E2E Tests**: 21
- **Workflow E2E Tests**: 14

## Test Categories

### Unit Tests (Current)

#### Configuration Module (`tests/test_config.py`)
- ✅ Default values loading
- ✅ Environment variable configuration
- ✅ JSON file configuration
- ✅ Fallback and default value handling

#### Authentication Module (`tests/test_auth.py`)
- ✅ Password authentication initialization
- ✅ OIDC authentication initialization
- ✅ Password retrieval
- ✅ Missing password handling
- ✅ Unknown auth type handling
- ✅ OIDC redirect URL configuration
- ✅ Configuration validation (password and OIDC)

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

### End-to-End Tests (New!)

Comprehensive E2E tests have been added for:

#### Main Entry Point (`main.py`)
- ✅ CLI argument parsing (--version, --help, flags)
- ✅ Configuration file loading and validation
- ✅ Show-config mode with output verification
- ✅ Verbose logging levels
- ✅ Color and redaction flags
- ✅ Admin users and allowed rooms flags
- ✅ Combined flag scenarios
- ✅ Error handling and user feedback

#### Workflow Tests
- ✅ Configuration wizard flow
- ✅ Multi-step command sequences
- ✅ Configuration migration scenarios
- ✅ Output formatting verification
- ✅ Error message clarity
- ✅ First-time user workflows

#### TUI Module (`tests/test_tui*.py`)

**New Comprehensive Pilot Tests (61 tests added!)**

Using Textual's pilot feature for automated TUI testing:

##### Core Application Tests (`tests/test_tui_pilot.py` - 44 tests)
- ✅ Main app startup and rendering
- ✅ Main menu button rendering and functionality
- ✅ All keyboard bindings (q, s, a, r, e, m, l, t, c, x)
- ✅ Theme application and switching
  - ✅ Default theme
  - ✅ Midnight theme
  - ✅ Grayscale theme
  - ✅ Windows 3.1 theme
  - ✅ MS-DOS theme
  - ✅ Invalid theme fallback
- ✅ Screen navigation
  - ✅ AdminsScreen display and navigation
  - ✅ RoomsScreen display and navigation
  - ✅ SessionsScreen display
  - ✅ SayScreen display
  - ✅ LogScreen display
  - ✅ SetScreen display
  - ✅ ShowScreen display
  - ✅ AliasesScreen display and navigation
  - ✅ OIDCAuthScreen display and special character handling
  - ✅ MessageScreen display and closing
- ✅ Widget functionality
  - ✅ BotStatusWidget rendering and updates
  - ✅ ActiveTasksWidget rendering and task display

##### Interactive Workflow Tests (`tests/test_tui_pilot_interactive.py` - 17 tests)
- ✅ Alias management workflows
  - ✅ Alias screen button selection
  - ✅ Keyboard navigation (b, escape)
- ✅ Multi-screen navigation
  - ✅ Multiple screen navigation sequence
  - ✅ Rapid navigation stress testing
  - ✅ Screen stack integrity verification
- ✅ Theme system validation
  - ✅ All themes render correctly
  - ✅ CSS variable completeness
- ✅ Widget updates
  - ✅ Active tasks widget dynamic updates
  - ✅ Bot status widget reactive updates
- ✅ Error handling
  - ✅ Graceful handling of missing bot
  - ✅ Graceful handling of missing Matrix client
- ✅ Keyboard shortcuts
  - ✅ All shortcuts trigger correct actions
  - ✅ Quit shortcuts functionality
- ✅ Application lifecycle
  - ✅ App startup validation
  - ✅ Metrics initialization
  - ✅ Login task handling

##### Existing Unit Tests (40 tests)
- ✅ Component creation and imports
- ✅ CSS compatibility across themes
- ✅ Menu screen functionality
- ✅ OIDC authentication screens
- ✅ CLI integration

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
├── test_config.py                 # Configuration tests
├── test_auth.py                   # Authentication tests
├── test_semaphore.py              # Semaphore client tests
├── test_bot.py                    # Bot tests
├── test_commands.py               # Command handler tests
├── test_messages.py               # Message template tests
├── test_aliases.py                # Command aliases tests
├── test_redactor.py               # Sensitive info redaction tests
├── test_verification.py           # Device verification tests
├── test_verification_e2e.py       # Verification E2E tests
├── test_tui.py                    # TUI unit tests
├── test_tui_menu_fixes.py         # TUI menu tests
├── test_tui_navigation.py         # TUI navigation tests
├── test_tui_pilot.py              # TUI pilot tests (NEW! 44 tests)
├── test_tui_pilot_interactive.py  # TUI interactive workflow tests (NEW! 17 tests)
├── test_cli.py                    # CLI argument tests
├── test_workflow.py               # GitHub workflow tests
├── test_e2e_main.py               # Main entry point E2E tests
└── test_e2e_workflow.py           # Workflow E2E tests
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Multiple Python versions (3.12, 3.13, 3.14)

See `.github/workflows/test.yml` for CI configuration.

## Coverage Goals

### Current Status
- ✅ Config: 71% (comprehensive unit tests)
- ✅ Auth: 100% (full password and OIDC coverage)
- ⏳ Semaphore: 68% (API methods tested, needs edge cases)
- ⏳ Bot: 52% (core functionality tested, needs more coverage)
- ⏳ Commands: 55% (command tests, needs workflow coverage)
- ✅ Main: 23% (E2E tests added! Up from 0%)
- ✅ Verification: 56% (device verification tested)
- ✅ Redactor: 93% (excellent coverage)
- ✅ Messages: 69% (message templates tested)
- ✅ Aliases: 71% (alias handling tested)
- ✅ TUI: Significantly improved with Textual pilot tests (61 new automated tests!)
- ✅ Overall: 40% (and improving!)

### Next Release Goals
- ⏳ Bot: 60%+ (additional edge cases and async flows)
- ⏳ Commands: 65%+ (more workflow coverage)
- ⏳ Main: 40%+ (more TUI and daemon mode E2E tests)
- ⏳ Overall: 50%+

### Long-term (Future)
- ⏳ Overall: 70%+
- ⏳ Full integration tests with Matrix server
- ⏳ End-to-end testing with Semaphore instance
- ⏳ Performance and stress testing
- ⏳ TUI interaction tests with textual pilot

## Known Limitations

1. **Async Mocking Complexity**: Some async tests with aiohttp are simplified to avoid complex mocking issues
2. **Matrix Server Required**: Full bot integration tests require a test Matrix server
3. **Semaphore Server Required**: Full Semaphore integration tests need a test Semaphore instance
4. **TUI Testing**: TUI tests have lower coverage (15%) due to interactive nature - textual pilot could be used for more coverage
5. **Config Wizard Testing**: Configuration wizard (0% coverage) requires interactive input testing

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
