---
layout: default
title: Contributing
nav_order: 6
---

# Contributing to ChatrixCD

Thank you for your interest in contributing to ChatrixCD! For comprehensive contribution guidelines including development setup, coding standards, and our AI/LLM development notice, see the full [CONTRIBUTING.md](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/CONTRIBUTING.md) in the repository root.

## How to Contribute

### Reporting Bugs

1. Check existing [issues](https://github.com/CJFWeatherhead/ChatrixCD/issues)
2. Create a new issue with:
   - Clear title
   - Detailed description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

### Suggesting Features

1. Check existing feature requests
2. Open a new issue with:
   - Feature description
   - Use cases
   - Possible implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Open a pull request

## Development Setup

### Prerequisites

- Python 3.12+ (3.12, 3.13, 3.14 supported)
- Git
- Virtual environment tool (venv or uv)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ChatrixCD.git
cd ChatrixCD

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run specific test file
python -m unittest tests.test_config -v

# Run specific test
python -m unittest tests.test_auth.TestMatrixAuth.test_init_password_auth -v
```

## Coding Standards

### Python Style

- Follow PEP 8
- Maximum line length: 100 characters
- Use type hints
- Add docstrings to public functions

### Code Example

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

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 72 characters
- Reference issues: "Fixes #123"

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

## Pull Request Process

1. Update CHANGELOG.md under "Unreleased" section
2. Update documentation if needed
3. Ensure all tests pass
4. Request review from maintainers
5. Address review feedback
6. Wait for approval and merge

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] CHANGELOG.md updated
- [ ] No new warnings
- [ ] Branding guidelines followed (if visual changes)

## Testing Guidelines

### Unit Tests

- Write tests for new functions
- Place in `tests/` directory
- Name files `test_<module_name>.py`
- Use descriptive test names

### Test Coverage

Current coverage goals:
- Config: 95%
- Auth: 80%
- Semaphore: 70%
- Bot: 40%

## Branding Guidelines

ChatrixCD maintains consistent visual branding. When contributing visual elements:

### Brand Colors

- **ChatrixCD Green**: `#4A9B7F` (primary)
- **Dark Background**: `#2D3238`
- **White**: `#FFFFFF`

### Logo Usage

- Use approved logos from `assets/` directory
- Follow placement and sizing guidelines
- Don't modify or distort logos

See [BRANDING.md](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/BRANDING.md) for complete guidelines.

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings
2. **User Documentation**: README, INSTALL, QUICKSTART
3. **Developer Documentation**: ARCHITECTURE, CONTRIBUTING
4. **Brand Documentation**: BRANDING (visual identity)
5. **API Documentation**: Docstrings

### Documentation Updates

Update relevant docs when making changes:
- README.md - Overview and features
- INSTALL.md - Installation steps
- QUICKSTART.md - Getting started
- ARCHITECTURE.md - Technical details
- CHANGELOG.md - Change history

## Project Structure

```
ChatrixCD/
├── .github/              # GitHub-specific files
│   ├── ISSUE_TEMPLATE/   # Issue templates
│   └── workflows/        # GitHub Actions
├── chatrixcd/            # Main package
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── bot.py           # Bot core
│   ├── auth.py          # Authentication
│   ├── config.py        # Configuration
│   ├── commands.py      # Commands
│   └── semaphore.py     # Semaphore client
├── tests/               # Test suite
├── docs/                # Documentation
└── README.md
```

## Getting Help

- [GitHub Discussions](https://github.com/CJFWeatherhead/ChatrixCD/discussions)
- [Issue Tracker](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- Read [ARCHITECTURE.md](architecture.html)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the GNU GPL v3.0.

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors page
- Release notes

Thank you for contributing to ChatrixCD! 🚀
