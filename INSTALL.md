# Installation Guide

This guide provides detailed instructions for installing and running ChatrixCD.

## Quick Start

### 1. Install uv (if not already installed)

```bash
# On Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Create Virtual Environment and Install Dependencies

```bash
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

### 3. Configure the Bot

```bash
cp config.json.example config.json
# Edit config.json with your settings
nano config.json
```

Configuration is done exclusively through JSON files (with HJSON support for comments).

### 4. Run the Bot

```bash
# Make sure your virtual environment is activated
chatrixcd
```

Or run directly:

```bash
python -m chatrixcd.main
```

For more control, use command-line options:

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

### Password Authentication

This is the simplest method for traditional Matrix servers:

1. Create a bot account on your Matrix server
2. Configure the credentials:
   ```json
   {
     "matrix": {
       "auth_type": "password",
       "user_id": "@chatrixcd:example.com",
       "password": "your_password"
     }
   }
   ```

### Token Authentication

If you have a pre-obtained access token:

1. Obtain an access token from your Matrix server
2. Configure the token:
   ```json
   {
     "matrix": {
       "auth_type": "token",
       "user_id": "@chatrixcd:example.com",
       "access_token": "your_access_token"
     }
   }
   ```

### OIDC Authentication

For Matrix servers that use OIDC/OAuth2:

1. Register an OAuth2 client with your OIDC provider
2. Configure OIDC settings:
   ```json
   {
     "matrix": {
       "auth_type": "oidc",
       "user_id": "@chatrixcd:example.com",
       "oidc_issuer": "https://auth.example.com",
       "oidc_client_id": "your_client_id",
       "oidc_client_secret": "your_client_secret"
     }
   }
   ```

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

### Authentication fails

- Verify your credentials are correct
- For OIDC: Ensure the OIDC provider is accessible
- For token auth: Verify the token hasn't expired
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
