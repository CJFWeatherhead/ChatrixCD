---
layout: default
title: Installation
nav_order: 2
---

# Installation Guide

This guide covers all installation methods for ChatrixCD. For more detailed platform-specific instructions and troubleshooting, see the comprehensive [INSTALL.md](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/INSTALL.md) in the repository root.

## Installation Methods

Choose the method that best suits your needs:

1. **Pre-built Binary** (Recommended) - Easiest, no Python required
2. **From Source** - For development or custom modifications
3. **Docker** - For containerized deployments

## Method 1: Pre-built Binary (Recommended)

The easiest way to get started - **no Python installation required!**

### Download

Download the appropriate binary for your platform:

#### Linux
- [x86_64 (64-bit)](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64) - Most common
- [i686 (32-bit)](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-i686)
- [ARM64](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-arm64) - Raspberry Pi, ARM servers

### Setup and Run

**Linux:**

```bash
# Download (example for Linux x86_64)
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64

# Make executable
chmod +x chatrixcd-linux-x86_64

# Run
./chatrixcd-linux-x86_64
```

On first run, create a `config.json` file in the same directory. See the [Configuration Guide](configuration.html) for details.

### Windows and macOS Users

Pre-built binaries are not currently available for Windows and macOS due to build complexity with native dependencies. Please use one of these alternatives:

#### Windows Installation Options

**Option A: Install from Source (Recommended)**
- Requires Python 3.12+ (see Method 2 below)
- Native Windows installation with full TUI support

**Option B: Windows Subsystem for Linux (WSL2)**
```powershell
# Install WSL2 (run as Administrator)
wsl --install

# After reboot, in WSL terminal:
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64
chmod +x chatrixcd-linux-x86_64
./chatrixcd-linux-x86_64
```

**Option C: Docker Desktop**
- Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- See Method 3 below for Docker instructions

#### macOS Installation Options

**Option A: Install from Source (Recommended)**
- Requires Python 3.12+ and homebrew (see Method 2 below)
- Native macOS installation with full TUI support

**Option B: Docker Desktop**
- Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- See Method 3 below for Docker instructions

## Method 2: Install from Source

For development, Windows/macOS users, or if you prefer to run from source.

### Prerequisites

- Python 3.12 or higher (3.12, 3.13, 3.14 supported)
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Access to a Matrix homeserver
- Access to a Semaphore UI instance with API access
- Platform-specific dependencies (see below)

### Platform-Specific Prerequisites

**macOS:**
```bash
# Install system dependencies via homebrew
brew install libolm pkg-config
```

**Windows:**
- libolm will be installed automatically via pip
- If you encounter build issues, consider using WSL2 or Docker instead

**Linux:**
- Most distributions include required dependencies
- If libolm is missing: `sudo apt install libolm-dev` (Debian/Ubuntu) or `sudo yum install libolm-devel` (RHEL/CentOS)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
# .venv\Scripts\activate.bat

# Install dependencies
uv pip install -r requirements.txt

# Install the application
uv pip install -e .
```

### Alternative: Install with pip

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the application
pip install -e .
```

## Method 3: Docker Installation

### Using Docker Compose (Debian-based)

```bash
# Clone the repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Create configuration file
cp config.json.example config.json
# Edit config.json with your settings

# Start with Docker Compose
docker-compose up -d
```

### Using Docker Compose (Alpine Linux)

For a minimal deployment:

```bash
docker-compose -f docker-compose.alpine.yml up -d
```

### Building Docker Image Manually

**Debian-based:**
```bash
docker build -t chatrixcd:latest .
docker run -v $(pwd)/config.json:/app/config.json -v $(pwd)/store:/app/store chatrixcd:latest
```

**Alpine Linux:**
```bash
docker build -f Dockerfile.alpine -t chatrixcd:alpine .
docker run -v $(pwd)/config.json:/app/config.json -v $(pwd)/store:/app/store chatrixcd:alpine
```

## Configuration

After installation, you need to configure ChatrixCD. See the [Configuration Guide](configuration.html) for details.

## Verification

Verify the installation:

```bash
chatrixcd --version
```

Or if running from source:

```bash
python -m chatrixcd.main --version
```

## Next Steps

- [Configure ChatrixCD](configuration.html)
- [Quick Start Guide](quickstart.html)
- [Deployment Options](deployment.html)

## Troubleshooting

If you encounter issues during installation:

1. Ensure Python 3.12+ is installed: `python --version`
2. Check that all dependencies are installed: `pip list`
3. Verify Matrix homeserver is accessible
4. Verify Semaphore UI API is accessible

For more help, see the [Support Guide](support.html).
