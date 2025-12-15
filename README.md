<div align="center">

<img src="assets/logo-horizontal.svg" alt="ChatrixCD Logo" width="600">


**Matrix bot for CI/CD automation through chat** 🚀

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-ChatrixCD-4A9B7F)](https://chatrix.cd/)

---

</div>

**ChatrixCD** connects Matrix chat with Semaphore UI to automate CI/CD tasks right from your chat room. It's like having a friendly bot coworker who handles your deployments! 🤖

## 🎯 Quick Start

**Just want to run it?** Here's the fastest path:

### 1. Install

**Linux (No Python needed!):**
```bash
# Download the binary for your architecture
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist
```

**From Source (Windows/macOS/Linux):**
```bash
pip install -e .
```

### 2. Configure

Create `config.json`:
```json
{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@mybot:matrix.org",
    "auth_type": "password",
    "password": "your-secure-password"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token"
  }
}
```

### 3. Run

```bash
./chatrixcd              # Linux binary
# OR
chatrixcd                # From source install
```

**That's it!** Invite your bot to a Matrix room and start running tasks. 🎉

## 📚 Need More?

- **[Full Installation Guide](https://chatrix.cd/installation.html)** - Detailed setup for all platforms
- **[Configuration Reference](https://chatrix.cd/configuration.html)** - All config options explained
- **[Quick Start Tutorial](https://chatrix.cd/quickstart.html)** - Step-by-step walkthrough
- **[Complete Documentation](https://chatrix.cd/)** - Everything you need to know

## ✨ Key Features

- 🔐 **End-to-End Encryption** - Secure Matrix rooms supported
- 🚀 **Semaphore Integration** - Start, monitor, and manage CI/CD tasks
- 💬 **Chat Commands** - Simple `!cd run`, `!cd status`, `!cd logs` 
- 🎯 **Smart Confirmations** - Thumbs up/down reactions or text
- 🔖 **Custom Aliases** - Create shortcuts for common tasks
- 🖥️ **Interactive TUI** - Terminal UI for bot management
- 🎭 **Fun Personality** - Sassy responses with emoji (never rude!)

## 🎮 Basic Commands

```bash
!cd help                           # Show all commands
!cd projects                       # List projects
!cd templates 1                    # List templates for project 1
!cd run 1 5                        # Run template 5 in project 1
!cd status                         # Check task status
!cd logs                           # View task logs
!cd stop 123                       # Stop task 123
```

### Advanced Run Options

- Positional tags: `!cd run 4 5 update,molecule`
- Flagged tags: `!cd run 4 5 --tags=update,molecule`
- Raw args: `!cd run 3 1 --args="--some --args -e"`

If the target template doesn’t support tags/arguments, the bot will let you know and suggest running without them.

## 🔧 Command Line Options

```bash
chatrixcd                          # Run with TUI (default)
chatrixcd -L                       # Log-only mode (no TUI)
chatrixcd -D                       # Daemon mode (background)
chatrixcd -C                       # Enable colored output
chatrixcd -v                       # Verbose logging
chatrixcd -s                       # Show current config
chatrixcd -c custom.json           # Use custom config file
```

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌────────────────┐
│   Matrix    │ ◄────── │  ChatrixCD   │ ──────► │  Semaphore UI  │
│   Server    │         │     Bot      │         │  REST API      │
└─────────────┘         └──────────────┘         └────────────────┘
     Chat                   Commands                   CI/CD Tasks
```

ChatrixCD sits between Matrix and Semaphore, translating chat commands into API calls and streaming results back to your room.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Found a bug? [Open an issue](https://github.com/CJFWeatherhead/ChatrixCD/issues)

## 📄 License

GNU General Public License v3.0 - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

- Built with [matrix-nio](https://github.com/poljar/matrix-nio)
- Integrates with [Semaphore UI](https://github.com/ansible-semaphore/semaphore)
- Inspired by [matrix-commander](https://github.com/8go/matrix-commander) for device verification and encryption handling patterns

### AI/LLM Contributions

**Important Notice:** Significant portions of this codebase were developed with assistance from AI/LLM tools, including:
- GitHub Copilot for code generation and completion
- Large Language Models (LLMs) for architecture design, documentation, and implementation
- AI-assisted code review and testing strategies

While AI tools accelerated development, all code has been reviewed, tested, and validated by human developers. Users should be aware that:
- Code patterns and documentation may reflect AI-generated content
- The project follows standard software engineering practices for testing and quality assurance
- Contributions and improvements from the community are welcome and encouraged

This transparency aligns with emerging best practices for AI-assisted software development.

---

<div align="center">

**Ready to automate your CI/CD through chat?** [Get Started →](https://chatrix.cd/)

</div>
