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
- 🖥️ **Interactive TUI**: Dual TUI modes - Turbo Vision-style (default) with menu bar and 3D windows, or classic interface
- 🧵 **Threaded Responses**: All bot replies are threaded for organized conversations
- 👍 **Reaction Confirmations**: Quick interactions with emoji reactions (👍/👎) for confirmations
- 🎭 **Fun Personality**: Varied greetings and sassy responses with emoji throughout
- 🚀 **Semaphore UI Integration**: Start and monitor CI/CD tasks via chat commands
- 📊 **Real-time Updates**: Automatic status updates for running tasks
- 🎯 **Command-based Interface**: Easy-to-use command system for task management
- 🔖 **Command Aliases**: Create custom shortcuts for frequently used commands
- ✅ **Task Confirmation**: Required confirmation before executing tasks with template details
- 🎨 **Rich Formatting**: Markdown and HTML formatting in messages with emoji support
- 🧠 **Smart Parameters**: Auto-fill project/template IDs when only one option available
- 📝 **Enhanced Logs**: Formatted output for Ansible and Terraform with intelligent tailing
- 🔧 **Flexible Configuration**: Support for HJSON config files (JSON with comments) with automatic migration
- ✅ **Configuration Validation**: Built-in schema validation with clear error messages
- 🔄 **Auto-Migration**: Automatic upgrade of configuration files when new features are added

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

- Python 3.12 or higher (3.12, 3.13, 3.14 supported)
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

- [GitHub Issues](https://github.com/CJFWeatherhead/ChatrixCD/issues) - Bug reports and feature requests
- [Support Guide](support.html) - Troubleshooting and getting help

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/LICENSE) file for details.
