# Quick Start Guide

Get ChatrixCD up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- A Matrix account for the bot
- Access to a Semaphore UI instance

## Installation

```bash
# Clone the repository
git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD

# Install dependencies
pip install -r requirements.txt

# Install the bot
pip install -e .
```

## Configuration

### For Password Authentication

Create a `.env` file:

```bash
cat > .env << EOF
MATRIX_HOMESERVER=https://matrix.example.com
MATRIX_USER_ID=@chatrixcd:example.com
MATRIX_AUTH_TYPE=password
MATRIX_PASSWORD=your_bot_password

SEMAPHORE_URL=https://semaphore.example.com
SEMAPHORE_API_TOKEN=your_api_token

BOT_COMMAND_PREFIX=!cd
EOF
```

### For OIDC Authentication

Create a `.env` file with OIDC settings:

```bash
cat > .env << EOF
MATRIX_HOMESERVER=https://matrix.example.com
MATRIX_USER_ID=@chatrixcd:example.com
MATRIX_AUTH_TYPE=oidc
MATRIX_OIDC_ISSUER=https://auth.example.com
MATRIX_OIDC_CLIENT_ID=your_client_id
MATRIX_OIDC_CLIENT_SECRET=your_client_secret

SEMAPHORE_URL=https://semaphore.example.com
SEMAPHORE_API_TOKEN=your_api_token

BOT_COMMAND_PREFIX=!cd
EOF
```

## Running the Bot

```bash
chatrixcd
```

The bot will:
1. Connect to your Matrix homeserver
2. Authenticate using your configured method
3. Start listening for commands

## Using the Bot

1. **Invite the bot to a room**
   - Open your Matrix client
   - Invite `@chatrixcd:example.com` to your room
   - The bot will auto-join

2. **Test the bot**
   ```
   !cd help
   ```

3. **List available projects**
   ```
   !cd projects
   ```

4. **View templates for a project**
   ```
   !cd templates 1
   ```

5. **Start a task**
   ```
   !cd run 1 5
   ```
   This starts task from project 1, template 5

6. **Monitor task status**
   The bot automatically reports status updates!
   You can also check manually:
   ```
   !cd status 123
   ```

## Docker Quick Start

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f chatrixcd
```

## Troubleshooting

### Bot doesn't start

Check your configuration:
```bash
python -c "from chatrixcd.config import Config; c = Config(); print(c.get_matrix_config())"
```

### Can't connect to Matrix

- Verify homeserver URL is correct
- Check credentials are valid
- Ensure network connectivity

### Can't connect to Semaphore

- Verify Semaphore URL is accessible
- Check API token is valid
- Test with: `curl -H "Authorization: Bearer YOUR_TOKEN" https://semaphore.example.com/api/projects`

### Bot doesn't respond to commands

- Check the command prefix (default: `!cd`)
- Verify bot has joined the room
- Check bot logs for errors

## Next Steps

- Read [INSTALL.md](INSTALL.md) for detailed installation options
- Review [README.md](README.md) for full documentation
- Configure access controls with `allowed_rooms` and `admin_users`

## Getting Help

- Check the logs: `tail -f chatrixcd.log`
- Review error messages in the Matrix room
- Open an issue on GitHub

## Example Session

```
User: !cd help
Bot: **ChatrixCD Bot Commands**
     !cd help - Show this help message
     !cd projects - List available projects
     ...

User: !cd projects
Bot: **Available Projects:**
     • My Web App (ID: 1)
     • Database Backup (ID: 2)

User: !cd templates 1
Bot: **Templates for Project 1:**
     • Deploy to Production (ID: 5)
     • Run Tests (ID: 6)

User: !cd run 1 5
Bot: Starting task from template 5...
     ✅ Task 123 started successfully!
     Use '!cd status 123' to check progress.

[10 seconds later]
Bot: 🔄 Task 123 is now running...

[2 minutes later]
Bot: ✅ Task 123 completed successfully!
```

Happy automating! 🚀
