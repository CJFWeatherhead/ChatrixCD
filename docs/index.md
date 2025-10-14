---
layout: default
title: Home
nav_order: 1
---

<div align="center" style="margin-bottom: 2em;">

<img src="assets/logo-horizontal.svg" alt="ChatrixCD Logo" width="500">

</div>


# ChatrixCD

**Matrix bot for CI/CD automation through chat**

---

## Features

- 🔐 **Native Matrix Authentication**: Support for password and OIDC/SSO authentication with Matrix servers
- 🔒 **E2E Encryption**: Full support for end-to-end encrypted Matrix rooms with device verification
- 🖥️ **Interactive TUI**: Text User Interface for bot management, monitoring, and configuration
- 🚀 **Semaphore UI Integration**: Start and monitor CI/CD tasks via chat commands
- 📊 **Real-time Updates**: Automatic status updates for running tasks
- 🎯 **Command-based Interface**: Easy-to-use command system for task management
- 🔧 **Flexible Configuration**: JSON config files with HJSON support (comments and trailing commas)

## Quick Links

- [Installation Guide](installation.html)
- [Quick Start](quickstart.html)
- [Configuration](configuration.html)
- [Architecture](architecture.html)
- [Contributing](contributing.html)
- [Security Policy](security.html)

## Getting Started

ChatrixCD makes it easy to manage CI/CD tasks through Matrix chat. Once installed and configured, you can:

1. Invite the bot to your Matrix room
2. List available projects with `!cd projects`
3. View templates with `!cd templates <project_id>`
4. Start tasks with `!cd run <project_id> <template_id>`
5. Monitor progress automatically

## Installation

### Prerequisites

- Python 3.9 or higher
- Access to a Matrix homeserver
- Access to a Semaphore UI instance with API access

### Quick Install

```bash
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

For detailed installation instructions, see the [Installation Guide](installation.html).

## Support

- [GitHub Issues](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- [Discussions](https://github.com/CJFWeatherhead/ChatrixCD/discussions)
- [Support Guide](support.html)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/LICENSE) file for details.
