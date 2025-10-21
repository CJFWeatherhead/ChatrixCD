# Installation Guide

This guide provides detailed instructions for installing and running ChatrixCD.

## Installation Methods

Choose the method that best suits your needs:

1. **Pre-built Binary** (Recommended) - Easiest, no Python required
2. **From Source** - For development or custom modifications
3. **Docker** - For containerized deployments

## Method 1: Pre-built Binary (Recommended)

The easiest way to get started - no Python installation required!

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
2. Double-click to run, or use Command Prompt/PowerShell:

```cmd
chatrixcd-windows-x86_64.exe
```

**First Run:**

On first run, the bot will create a sample configuration file if one doesn't exist. You'll need to:

1. Stop the bot (Ctrl+C)
2. Edit `config.json` with your Matrix and Semaphore credentials
3. Restart the bot

Continue to the [Configuration](#configuration) section below.

## Method 2: Install from Source

For development or if you prefer to run from source.

### Prerequisites

- Python 3.12 or higher (3.12, 3.13, 3.14 supported)
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended) or pip

### Prerequisites

- Python 3.12 or higher (3.12, 3.13, 3.14 supported)
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer (recommended) or pip

### Install uv (if not already installed)

```bash
# On Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

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
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Install the application
uv pip install -e .
```

## Method 3: Docker Installation

For containerized deployments.

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

After installation (any method), you need to configure ChatrixCD.

## Configuration

After installation (any method), you need to configure ChatrixCD.

### Create Configuration File

**For binary installations:**
The binary will look for `config.json` in the current directory. Create it from the example:

```bash
# Download example config
wget https://raw.githubusercontent.com/CJFWeatherhead/ChatrixCD/main/config.json.example -O config.json

# Or if you cloned the repo:
cp config.json.example config.json
```

**For source/Docker installations:**
```bash
cp config.json.example config.json
```

Edit `config.json` with your settings:

```bash
nano config.json  # or use your preferred editor
```

Configuration is done exclusively through JSON files (with HJSON support for comments).

## Running the Bot

### From Binary

```bash
# Linux/macOS (adjust filename for your platform)
./chatrixcd-linux-x86_64

# With options
./chatrixcd-linux-x86_64 --help
./chatrixcd-linux-x86_64 -c /path/to/config.json
./chatrixcd-linux-x86_64 -L  # Log-only mode (no TUI)
```

```cmd
rem Windows
chatrixcd-windows-x86_64.exe

rem With options
chatrixcd-windows-x86_64.exe --help
chatrixcd-windows-x86_64.exe -c C:\path\to\config.json
```

### From Source

**Interactive Mode (with TUI):**

```bash
# Make sure your virtual environment is activated
chatrixcd

# Or with colored output
chatrixcd -C
```

**Classic Log-Only Mode:**

```bash
# Run without TUI (classic behavior)
chatrixcd -L
```

Or run directly:

```bash
python -m chatrixcd.main
```

### Command-Line Options

All installation methods support these options:

```bash
# Show help
chatrixcd --help

# Show version
chatrixcd --version

# Run with verbose logging
chatrixcd -v

# Use custom config file
chatrixcd -c /path/to/config.json

# Run in daemon mode (Unix/Linux only)
chatrixcd -D

# Display configuration (credentials redacted)
chatrixcd -s
```

## Authentication Setup

ChatrixCD supports two authentication methods:

### Password Authentication

This is the simplest and most common method:

1. Create a bot account on your Matrix server
2. Configure the credentials in `config.json`:
   ```json
   {
     "matrix": {
       "homeserver": "https://matrix.example.com",
       "user_id": "@chatrixcd:example.com",
       "auth_type": "password",
       "password": "your_password",
       "store_path": "./store"
     }
   }
   ```

### OIDC/SSO Authentication

For Matrix servers that use OIDC/Single Sign-On (like some enterprise deployments):

1. Configure OIDC settings in `config.json`:
   ```json
   {
     "matrix": {
       "homeserver": "https://matrix.example.com",
       "user_id": "@chatrixcd:example.com",
       "auth_type": "oidc",
       "oidc_redirect_url": "http://localhost:8080/callback",  // Optional
       "store_path": "./store"
     }
   }
   ```

2. When you start the bot:
   - The bot will display an SSO authentication URL
   - Open the URL in your browser
   - Complete the authentication with your OIDC provider
   - Copy the callback URL (it will contain a `loginToken` parameter)
   - Paste the URL or just the token back into the bot

3. The bot will complete the login automatically

#### Understanding `oidc_redirect_url`

The `oidc_redirect_url` is the URL where the Matrix server will redirect your browser after successful authentication. **This field is optional** and defaults to `http://localhost:8080/callback` if not specified.

**Important:** The redirect URL does not need to be a running web server. It's simply used to receive the `loginToken` parameter in the URL. When the authentication completes, you copy the entire callback URL (or just the token) and paste it back into ChatrixCD.

**Common redirect URL patterns:**

- **Local development/testing:** `http://localhost:8080/callback` (default)
  - No web server needed
  - Works for desktop/local deployments
  
- **Production with web handler:** `https://your-domain.com/auth/callback`
  - If you want to build a web page that automatically extracts and submits the token
  - Requires setting up a simple web server/page
  
- **Out-of-band (CLI apps):** `urn:ietf:wg:oauth:2.0:oob`
  - Standard OAuth2 redirect for command-line applications
  - Some Matrix servers may not support this

**For most users:** Leave `oidc_redirect_url` unset or use the default. The token will appear in your browser's address bar, and you simply copy/paste it.

## Docker Deployment

### Using Docker Compose

1. Create configuration file:
   ```bash
   cp config.json.example config.json
   # Edit config.json with your settings
   ```

2. Update docker-compose.yml to mount the config file (uncomment the config mount line):
   ```yaml
   volumes:
     - ./store:/app/store
     - ./config.json:/app/config.json:ro  # Uncomment this line
   ```

3. Start the bot:
   ```bash
   docker-compose up -d
   ```

4. View logs:
   ```bash
   docker-compose logs -f chatrixcd
   ```

### Using Docker Directly

```bash
docker build -t chatrixcd .
docker run -d \
  --name chatrixcd \
  -v $(pwd)/store:/app/store \
  -e MATRIX_HOMESERVER=https://matrix.example.com \
  -e MATRIX_USER_ID=@chatrixcd:example.com \
  -e MATRIX_PASSWORD=your_password \
  -e SEMAPHORE_URL=https://semaphore.example.com \
  -e SEMAPHORE_API_TOKEN=your_token \
  chatrixcd
```

## Systemd Service (Linux)

For production deployments on Linux using systemd (Ubuntu, Debian, RHEL, CentOS, Fedora, etc.):

1. Create a user for the bot:
   ```bash
   sudo useradd -r -s /bin/false chatrixcd
   ```

2. Install uv and the bot:
   ```bash
   sudo mkdir -p /opt/chatrixcd
   sudo cp -r . /opt/chatrixcd/
   
   # Install uv as the chatrixcd user
   sudo -u chatrixcd curl -LsSf https://astral.sh/uv/install.sh | sudo -u chatrixcd sh
   
   # Create virtual environment using uv
   cd /opt/chatrixcd
   sudo -u chatrixcd ~/.cargo/bin/uv venv .venv
   
   # Install dependencies
   sudo -u chatrixcd ~/.cargo/bin/uv pip install -r /opt/chatrixcd/requirements.txt
   sudo -u chatrixcd ~/.cargo/bin/uv pip install -e /opt/chatrixcd
   ```

3. Create configuration:
   ```bash
   sudo cp config.json.example /opt/chatrixcd/config.json
   sudo nano /opt/chatrixcd/config.json
   ```

4. Set permissions:
   ```bash
   sudo chown -R chatrixcd:chatrixcd /opt/chatrixcd
   sudo mkdir -p /opt/chatrixcd/store
   sudo chown chatrixcd:chatrixcd /opt/chatrixcd/store
   ```

5. Install and start the service:
   ```bash
   sudo cp chatrixcd.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable chatrixcd
   sudo systemctl start chatrixcd
   ```

6. Check status:
   ```bash
   sudo systemctl status chatrixcd
   sudo journalctl -u chatrixcd -f
   ```

## Debian-Specific Deployment

For Debian systems with enhanced security:

1. Install required packages:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv git curl
   ```

2. Create a dedicated user:
   ```bash
   sudo useradd -r -m -d /opt/chatrixcd -s /bin/false chatrixcd
   ```

3. Install ChatrixCD:
   ```bash
   sudo -u chatrixcd git clone https://github.com/CJFWeatherhead/ChatrixCD.git /opt/chatrixcd/app
   cd /opt/chatrixcd/app
   
   # Create virtual environment
   sudo -u chatrixcd python3 -m venv /opt/chatrixcd/.venv
   
   # Install dependencies
   sudo -u chatrixcd /opt/chatrixcd/.venv/bin/pip install -r requirements.txt
   sudo -u chatrixcd /opt/chatrixcd/.venv/bin/pip install -e .
   ```

4. Configure the bot:
   ```bash
   sudo -u chatrixcd cp /opt/chatrixcd/app/config.json.example /opt/chatrixcd/config.json
   sudo -u chatrixcd nano /opt/chatrixcd/config.json
   ```

5. Create store directory:
   ```bash
   sudo -u chatrixcd mkdir -p /opt/chatrixcd/store
   ```

6. Install and enable systemd service:
   ```bash
   sudo cp /opt/chatrixcd/app/chatrixcd-debian.service /etc/systemd/system/chatrixcd.service
   sudo systemctl daemon-reload
   sudo systemctl enable chatrixcd
   sudo systemctl start chatrixcd
   ```

7. Verify the service:
   ```bash
   sudo systemctl status chatrixcd
   sudo journalctl -u chatrixcd -f
   ```

## Alpine Linux Deployment

Alpine Linux uses OpenRC instead of systemd. This is a lightweight deployment option.

### Using Docker on Alpine (Recommended)

1. Install Docker:
   ```bash
   apk add docker docker-compose
   rc-update add docker default
   rc-service docker start
   ```

2. Build Alpine-optimized image:
   ```bash
   docker build -f Dockerfile.alpine -t chatrixcd:alpine .
   ```

3. Run the container:
   ```bash
   docker run -d \
     --name chatrixcd \
     -v /opt/chatrixcd/store:/app/store \
     -e MATRIX_HOMESERVER=https://matrix.example.com \
     -e MATRIX_USER_ID=@chatrixcd:example.com \
     -e MATRIX_PASSWORD=your_password \
     -e SEMAPHORE_URL=https://semaphore.example.com \
     -e SEMAPHORE_API_TOKEN=your_token \
     --restart unless-stopped \
     chatrixcd:alpine
   ```

### Native Alpine Installation with OpenRC

1. Install required packages:
   ```bash
   apk add python3 py3-pip py3-virtualenv git gcc musl-dev libffi-dev openssl-dev
   ```

2. Create a dedicated user:
   ```bash
   adduser -D -h /opt/chatrixcd -s /sbin/nologin chatrixcd
   ```

3. Install ChatrixCD:
   ```bash
   su - chatrixcd -s /bin/sh -c "cd /opt/chatrixcd && git clone https://github.com/CJFWeatherhead/ChatrixCD.git app"
   cd /opt/chatrixcd/app
   
   # Create virtual environment
   su - chatrixcd -s /bin/sh -c "python3 -m venv /opt/chatrixcd/.venv"
   
   # Install dependencies
   su - chatrixcd -s /bin/sh -c "/opt/chatrixcd/.venv/bin/pip install -r /opt/chatrixcd/app/requirements.txt"
   su - chatrixcd -s /bin/sh -c "/opt/chatrixcd/.venv/bin/pip install -e /opt/chatrixcd/app"
   ```

4. Configure the bot:
   ```bash
   su - chatrixcd -s /bin/sh -c "cp /opt/chatrixcd/app/config.json.example /opt/chatrixcd/config.json"
   su - chatrixcd -s /bin/sh -c "vi /opt/chatrixcd/config.json"
   ```

5. Create log directory:
   ```bash
   mkdir -p /var/log/chatrixcd
   chown chatrixcd:chatrixcd /var/log/chatrixcd
   ```

6. Install and enable OpenRC service:
   ```bash
   cp /opt/chatrixcd/app/chatrixcd.initd /etc/init.d/chatrixcd
   chmod +x /etc/init.d/chatrixcd
   rc-update add chatrixcd default
   rc-service chatrixcd start
   ```

7. Check service status:
   ```bash
   rc-service chatrixcd status
   tail -f /var/log/chatrixcd/chatrixcd.log
   ```

## Semaphore UI Setup

1. Log into your Semaphore UI instance
2. Go to User Settings → API Tokens
3. Create a new API token
4. Copy the token to your configuration

## Testing the Bot

1. Start the bot
2. Invite the bot to a Matrix room
3. Send a test command:
   ```
   !cd help
   ```
4. The bot should respond with available commands

## Troubleshooting

### Bot doesn't respond

- Check that the bot is running: `sudo systemctl status chatrixcd` (systemd) or `docker-compose logs chatrixcd` (Docker)
- Verify the bot has joined the room
- Check the command prefix matches your configuration
- Review logs for errors
- Enable verbose logging: `chatrixcd -vv` or `chatrixcd -vv -R` (with redaction for privacy)

### Authentication fails

- Verify your credentials are correct
- For OIDC: Follow the SSO authentication flow carefully
- For password auth: Ensure the password is correct
- Check the homeserver URL is correct

### Can't connect to Semaphore

- Verify the Semaphore URL is accessible from the bot
- Check the API token is valid
- Ensure the bot has network access to Semaphore

### E2E Encryption issues

- The `store` directory must persist between restarts
- Ensure the bot account has verified its device
- Check file permissions on the store directory

## Security Best Practices

1. **Protect credentials**: Never commit config.json with real credentials
2. **Use restricted tokens**: Create Semaphore API tokens with minimal required permissions
3. **Secure the store**: The store directory contains encryption keys - keep it secure
4. **Access control**: Use `allowed_rooms` and `admin_users` to restrict bot access
5. **Regular updates**: Keep dependencies updated for security patches
6. **Network security**: Use HTTPS for all endpoints
7. **Monitoring**: Set up logging and monitoring for the bot
8. **Log redaction**: When sharing logs for troubleshooting, use `-R` flag to redact sensitive information:
   ```bash
   chatrixcd -vv -R  # Verbose logging with automatic redaction
   ```

## Upgrading

To upgrade ChatrixCD:

```bash
# Pull latest changes
git pull

# Activate virtual environment if not already activated
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate    # On Windows

# Upgrade dependencies
uv pip install -r requirements.txt --upgrade

# Restart the bot
```

For Docker:
```bash
docker-compose pull
docker-compose up -d
```

For systemd:
```bash
cd /opt/chatrixcd
sudo -u chatrixcd git pull
sudo -u chatrixcd ~/.cargo/bin/uv pip install -r requirements.txt --upgrade
sudo systemctl restart chatrixcd
```
