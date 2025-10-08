# Installation Guide

This guide provides detailed instructions for installing and running ChatrixCD.

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Bot

Choose one of the following configuration methods:

#### Option A: Using Environment Variables

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

#### Option B: Using YAML Configuration

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
nano config.yaml
```

### 3. Run the Bot

```bash
python -m chatrixcd.main
```

Or install and use the command:

```bash
pip install -e .
chatrixcd
```

## Authentication Setup

### Password Authentication

This is the simplest method for traditional Matrix servers:

1. Create a bot account on your Matrix server
2. Configure the credentials:
   ```yaml
   matrix:
     auth_type: "password"
     user_id: "@chatrixcd:example.com"
     password: "your_password"
   ```

### Token Authentication

If you have a pre-obtained access token:

1. Obtain an access token from your Matrix server
2. Configure the token:
   ```yaml
   matrix:
     auth_type: "token"
     user_id: "@chatrixcd:example.com"
     access_token: "your_access_token"
   ```

### OIDC Authentication

For Matrix servers that use OIDC/OAuth2:

1. Register an OAuth2 client with your OIDC provider
2. Configure OIDC settings:
   ```yaml
   matrix:
     auth_type: "oidc"
     user_id: "@chatrixcd:example.com"
     oidc_issuer: "https://auth.example.com"
     oidc_client_id: "your_client_id"
     oidc_client_secret: "your_client_secret"
   ```

## Docker Deployment

### Using Docker Compose

1. Copy environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. Start the bot:
   ```bash
   docker-compose up -d
   ```

3. View logs:
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

For production deployments on Linux:

1. Create a user for the bot:
   ```bash
   sudo useradd -r -s /bin/false chatrixcd
   ```

2. Install the bot:
   ```bash
   sudo mkdir -p /opt/chatrixcd
   sudo cp -r . /opt/chatrixcd/
   sudo python3 -m venv /opt/chatrixcd/venv
   sudo /opt/chatrixcd/venv/bin/pip install -r /opt/chatrixcd/requirements.txt
   sudo /opt/chatrixcd/venv/bin/pip install -e /opt/chatrixcd
   ```

3. Create configuration:
   ```bash
   sudo cp config.yaml.example /opt/chatrixcd/config.yaml
   sudo nano /opt/chatrixcd/config.yaml
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

1. **Protect credentials**: Never commit config.yaml or .env files with real credentials
2. **Use restricted tokens**: Create Semaphore API tokens with minimal required permissions
3. **Secure the store**: The store directory contains encryption keys - keep it secure
4. **Access control**: Use `allowed_rooms` and `admin_users` to restrict bot access
5. **Regular updates**: Keep dependencies updated for security patches
6. **Network security**: Use HTTPS for all endpoints
7. **Monitoring**: Set up logging and monitoring for the bot

## Upgrading

To upgrade ChatrixCD:

```bash
git pull
pip install -r requirements.txt --upgrade
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
sudo -u chatrixcd /opt/chatrixcd/venv/bin/pip install -r requirements.txt --upgrade
sudo systemctl restart chatrixcd
```
