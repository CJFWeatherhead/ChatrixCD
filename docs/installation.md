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

#### Windows
- [x86_64 (64-bit)](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-windows-x86_64.exe)
- [ARM64](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-windows-arm64.exe)

#### macOS
- [Universal Binary](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-macos-universal) - Intel and Apple Silicon

### Setup and Run

**Linux/macOS:**

```bash
# Download (example for Linux x86_64)
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64

# Make executable
chmod +x chatrixcd-linux-x86_64

# Run
./chatrixcd-linux-x86_64
```

**Windows:**

1. Download the appropriate `.exe` file
2. Double-click to run, or use Command Prompt/PowerShell

On first run, create a `config.json` file in the same directory. See the [Configuration Guide](configuration.html) for details.

## Method 2: Install from Source

For development or if you prefer to run from source.

### Prerequisites

- Python 3.12 or higher (3.12, 3.13, 3.14 supported)
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Access to a Matrix homeserver
- Access to a Semaphore UI instance with API access

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
# On Windows:
# .venv\Scripts\activate

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
