# Contributing to ChatrixCD

Thank you for your interest in contributing to ChatrixCD! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior by opening an issue or contacting the repository maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/CJFWeatherhead/ChatrixCD/issues) to avoid duplicates.

When you are creating a bug report, please include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed and what behavior you expected
- Include logs, screenshots, or error messages if applicable
- Note your environment (OS, Python version, Matrix homeserver type, etc.)

Use the bug report issue template when available.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear and descriptive title
- Provide a detailed description of the suggested enhancement
- Explain why this enhancement would be useful
- List any alternative solutions or features you've considered
- Include examples of how the feature would be used

Use the feature request issue template when available.

### Pull Requests

We actively welcome your pull requests:

1. Fork the repository and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the project's style guidelines
6. Issue the pull request!

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- Git
- A Matrix homeserver account for testing
- (Optional) A Semaphore UI instance for integration testing

### Initial Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/ChatrixCD.git
   cd ChatrixCD
   ```

2. **Create a virtual environment**

   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   # .venv\Scripts\activate    # On Windows
   ```

3. **Install dependencies**

   ```bash
   uv pip install -r requirements.txt
   uv pip install -e .
   ```

4. **Set up test configuration**

   ```bash
   cp config.json.example config.json
   cp .env.example .env
   # Edit these files with your test credentials
   ```

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest tests.test_config

# Run with verbose output
python -m unittest discover -v
```

### Running the Bot Locally

```bash
# Using the installed package
chatrixcd

# Or directly with Python
python -m chatrixcd.main
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all public functions, classes, and modules
- Keep functions focused and single-purpose
- Maximum line length: 100 characters (flexible for readability)

### Code Style Examples

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Implementation
    return True
```

### Documentation

- Add docstrings following Google or NumPy style
- Update README.md if you add new features
- Update relevant documentation files (INSTALL.md, QUICKSTART.md, ARCHITECTURE.md)
- Include code comments for complex logic

### Commit Messages

Write clear, concise commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
Add OIDC refresh token support

- Implement token refresh logic in auth.py
- Add tests for token refresh
- Update documentation

Fixes #123
```

### Branch Naming

Use descriptive branch names:

- `feature/add-task-scheduling` - for new features
- `fix/authentication-error` - for bug fixes
- `docs/update-install-guide` - for documentation
- `refactor/command-handler` - for refactoring

## Submitting Changes

### Before Submitting

1. **Test your changes**
   ```bash
   python -m unittest discover
   ```

2. **Check code style** (if you have tools installed)
   ```bash
   # Optional: Use pylint, flake8, or black
   flake8 chatrixcd/
   ```

3. **Update documentation** if needed

4. **Commit your changes** with clear messages

### Pull Request Process

1. **Update the CHANGELOG.md** with notes on your changes under the "Unreleased" section

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request** from your fork to the main repository

4. **Fill in the PR template** with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if UI changes)

5. **Respond to review feedback** - maintainers may request changes

6. **Wait for CI checks** - automated tests must pass

### Pull Request Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code performed
- [ ] Comments added for complex code
- [ ] Documentation updated (if applicable)
- [ ] Tests added/updated (if applicable)
- [ ] All tests pass locally
- [ ] CHANGELOG.md updated
- [ ] No new warnings introduced

## Testing Guidelines

### Unit Tests

- Write unit tests for new functions and classes
- Place tests in the `tests/` directory
- Name test files `test_<module_name>.py`
- Use descriptive test method names

Example:
```python
import unittest
from chatrixcd.config import Config

class TestConfig(unittest.TestCase):
    def test_load_config_from_env(self):
        """Test configuration loading from environment variables."""
        # Test implementation
        pass
```

### Integration Tests

- Integration tests should test interactions between components
- Mock external services (Matrix homeserver, Semaphore API) when possible
- Document any required test setup

### Manual Testing

For changes that affect the bot's behavior:

1. Test with a real Matrix room
2. Verify command responses
3. Check log output
4. Test error conditions

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: README.md, INSTALL.md, QUICKSTART.md
3. **Developer Documentation**: ARCHITECTURE.md, this file
4. **API Documentation**: Docstrings in source code

### Documentation Updates

When making changes, consider updating:

- **README.md**: Overview, features, basic usage
- **INSTALL.md**: Installation and configuration details
- **QUICKSTART.md**: Getting started guide
- **ARCHITECTURE.md**: Technical architecture details
- **CHANGELOG.md**: Record of changes

## Project Structure

```
ChatrixCD/
├── .github/              # GitHub-specific files
│   ├── ISSUE_TEMPLATE/   # Issue templates
│   └── workflows/        # GitHub Actions workflows
├── chatrixcd/            # Main package
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── bot.py           # Bot core logic
│   ├── auth.py          # Authentication handling
│   ├── config.py        # Configuration management
│   ├── commands.py      # Command handlers
│   └── semaphore.py     # Semaphore API client
├── tests/               # Test suite
│   ├── __init__.py
│   └── test_*.py        # Test files
├── ARCHITECTURE.md      # Architecture documentation
├── CHANGELOG.md         # Project changelog
├── CODE_OF_CONDUCT.md   # Code of conduct
├── CONTRIBUTING.md      # This file
├── INSTALL.md           # Installation guide
├── LICENSE              # GPL-3.0 license
├── QUICKSTART.md        # Quick start guide
├── README.md            # Project overview
├── SECURITY.md          # Security policy
├── requirements.txt     # Python dependencies
└── setup.py             # Package setup
```

## Getting Help

### Resources

- **Documentation**: Check README.md, INSTALL.md, and other docs
- **Issues**: Search [existing issues](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- **Discussions**: Open a discussion for questions

### Asking Questions

When asking for help:

1. Check documentation first
2. Search for similar issues
3. Provide context and details
4. Include relevant code or logs
5. Describe what you've tried

## Recognition

Contributors will be:

- Listed in release notes for their contributions
- Credited in the project's acknowledgments
- Recognized in commit history

## License

By contributing to ChatrixCD, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## Development Roadmap

Check the [CHANGELOG.md](CHANGELOG.md) "Unreleased" section and [open issues](https://github.com/CJFWeatherhead/ChatrixCD/issues) for planned features and improvements.

### Current Focus Areas

- Adding more comprehensive tests
- Improving error handling
- Expanding command functionality
- Supporting additional CI/CD platforms
- Enhancing documentation

## Thank You!

Thank you for contributing to ChatrixCD! Every contribution helps make this project better for everyone. 🚀
