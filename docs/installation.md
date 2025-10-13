---
layout: default
title: Installation
nav_order: 2
---

# Installation Guide

This guide covers all installation methods for ChatrixCD.

## Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended)
- Access to a Matrix homeserver
- Access to a Semaphore UI instance with API access

## Installation Methods

### Install from Source (Recommended)

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

### Install with pip

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the application
pip install -e .
```

## Docker Installation

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

1. Ensure Python 3.9+ is installed: `python --version`
2. Check that all dependencies are installed: `pip list`
3. Verify Matrix homeserver is accessible
4. Verify Semaphore UI API is accessible

For more help, see the [Support Guide](support.html).
