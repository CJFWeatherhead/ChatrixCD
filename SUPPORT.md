# Support

Thank you for using ChatrixCD! This document provides information on how to get help with the project.

## Documentation

Before seeking help, please check the following documentation:

- **[README.md](README.md)** - Project overview and features
- **[INSTALL.md](INSTALL.md)** - Detailed installation and configuration guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide to get up and running
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details
- **[TROUBLESHOOTING](#troubleshooting)** - Common issues and solutions (see below)

## Getting Help

### Asking Questions

If you have questions about using ChatrixCD:

1. **Check the documentation** - Many common questions are already answered
2. **Search existing issues** - Someone may have already asked the same question
3. **Open an Issue** - Use [GitHub Issues](https://github.com/CJFWeatherhead/ChatrixCD/issues) for questions and support

### Reporting Bugs

If you've found a bug:

1. **Search existing issues** - Check if the bug has already been reported
2. **Use the bug report template** - [Create a bug report](https://github.com/CJFWeatherhead/ChatrixCD/issues/new/choose)
3. **Provide details** - Include logs, configuration (without credentials), and steps to reproduce
4. **Protect your privacy** - Use the `-R` flag when collecting logs to automatically redact sensitive information:
   ```bash
   chatrixcd -vv -R  # Verbose logging with redaction
   ```

### Requesting Features

To suggest a new feature:

1. **Check existing issues** - The feature may already be planned
2. **Use the feature request template** - [Create a feature request](https://github.com/CJFWeatherhead/ChatrixCD/issues/new/choose)
3. **Explain the use case** - Help us understand why this feature would be valuable

### Security Issues

For security vulnerabilities:

- **Do not create public issues**
- Follow the [Security Policy](SECURITY.md)
- Use GitHub's private vulnerability reporting or contact maintainers directly

## Troubleshooting

### Common Issues

#### Bot doesn't respond to commands

**Symptoms**: Bot is online but doesn't respond to commands

**Solutions**:
- Verify the bot has joined the room
- Check the command prefix in your configuration matches what you're using
- Review logs for errors: `tail -f chatrixcd.log`
- Ensure the bot account has permission to read messages
- If using `allowed_rooms`, verify the room is in the list

#### Authentication fails

**Symptoms**: Bot can't log in to Matrix homeserver

**Solutions**:
- Verify credentials are correct (username, password, or token)
- Check homeserver URL is correct and accessible
- For OIDC: Ensure the OIDC provider URL is correct
- For OIDC: Verify client ID and secret are valid
- Check network connectivity to homeserver
- Review authentication logs for specific errors

#### Can't connect to Semaphore

**Symptoms**: Bot connects to Matrix but can't communicate with Semaphore UI

**Solutions**:
- Verify Semaphore URL is correct and accessible
- Check Semaphore API token is valid
- Ensure the bot has network access to Semaphore
- Test Semaphore API manually: `curl -H "Authorization: Bearer YOUR_TOKEN" https://semaphore.example.com/api/ping`
- Check Semaphore logs for API errors

**SSL Certificate Errors**: If you see `SSLCertVerificationError` or `certificate verify failed`:
- For self-signed certificates: Set `"ssl_verify": false` in the semaphore configuration
- For custom CA: Set `"ssl_ca_cert": "/path/to/ca.crt"` in the semaphore configuration
- For mutual TLS: Configure both `"ssl_client_cert"` and `"ssl_client_key"` in the semaphore configuration
- See the [SSL/TLS Configuration](docs/configuration.md#ssltls-configuration-for-semaphore) section in the documentation for more details

#### E2E Encryption issues

**Symptoms**: Bot can't read encrypted messages or fails to send encrypted messages

**How it works**:
- The bot automatically uploads encryption keys and queries device keys after login
- The bot requests encryption keys when it receives encrypted messages it cannot decrypt
- After keys are received, messages will be decrypted on the next sync
- First-time messages in encrypted rooms may take a moment to decrypt as keys are exchanged
- The bot tracks requested session IDs to avoid duplicate key requests

**Solutions**:
- Wait a few seconds after sending a command - the bot may need to request and receive encryption keys
- Ensure the `store` directory persists between restarts
- Check file permissions on the store directory: `ls -la store/`
- Look for "Uploading encryption keys..." or "Querying device keys..." in logs after login
- Check logs for "Unable to decrypt message" warnings - these are normal initially
- Verify the bot account has verified its device (not currently required but recommended)
- If problems persist after initial key exchange, clear the store and re-verify (last resort - loses encrypted message history)
- Check that `store_path` in configuration points to a writable location

#### Task doesn't start

**Symptoms**: `!cd run` command fails or task doesn't appear in Semaphore

**Solutions**:
- Verify project ID and template ID are correct
- Check that the Semaphore user (API token owner) has access to the project
- Ensure the template is configured correctly in Semaphore
- Review Semaphore UI task history for errors
- Check Semaphore logs for API errors

#### Bot crashes or exits unexpectedly

**Symptoms**: Bot process terminates without warning

**Solutions**:
- Check bot logs for error messages
- Verify Python version is 3.12 or higher (3.12, 3.13, 3.14 supported)
- Ensure all dependencies are installed: `uv pip install --python .venv/bin/python -r requirements.txt`
- Check system resources (memory, disk space)
- Review systemd journal if using systemd: `journalctl -u chatrixcd -n 100`

### Debugging

#### Enable verbose logging

Use command-line flags for verbose logging:

```bash
# Basic verbose logging
chatrixcd -v

# More verbose with library logs
chatrixcd -vv

# Verbose with redaction (recommended for sharing logs)
chatrixcd -vv -R

# Verbose with redaction and colored output (redacted parts in pink)
chatrixcd -vv -C -R
```

Or add to your configuration:

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

#### Check logs

**Direct execution**:
```bash
tail -f chatrixcd.log
```

**Docker**:
```bash
docker-compose logs -f chatrixcd
```

**Systemd**:
```bash
journalctl -u chatrixcd -f
```

#### Test connectivity

**Test Matrix homeserver**:
```bash
curl https://your-homeserver.com/.well-known/matrix/client
```

**Test Semaphore API**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://semaphore.example.com/api/ping
```

#### Verify configuration

```bash
# Check configuration loading
python -c "from chatrixcd.config import Config; c = Config(); print(c.get_matrix_config())"
```

### Getting More Help

If you're still stuck after trying the above:

1. **Gather information**:
   - Exact error messages
   - Relevant logs (with credentials removed)
   - Configuration details (with credentials removed)
   - Environment details (OS, Python version, deployment method)

2. **Create a detailed issue**:
   - Use the bug report template
   - Include all gathered information
   - Describe what you've already tried

3. **Be patient**:
   - This is an open-source project maintained by volunteers
   - Response times may vary
   - Consider contributing fixes if you solve the issue!

## Community

### Contributing

If you'd like to contribute to the project:

- Read the [Contributing Guide](CONTRIBUTING.md)
- Check the [Code of Conduct](CODE_OF_CONDUCT.md)
- Look for issues labeled "good first issue" or "help wanted"

### Staying Updated

- **Watch the repository** for notifications about new releases
- **Star the repository** to bookmark it
- **Follow releases** to be notified of new versions

## Commercial Support

This is a community-driven open-source project. Commercial support is not currently available, but contributions and sponsorships are welcome!

## Response Times

This is an open-source project maintained by volunteers:

- **Bug reports**: We aim to respond within a week
- **Feature requests**: We'll review and provide feedback when possible
- **Security issues**: We aim to respond within 48 hours
- **Pull requests**: We'll review as time permits

Thank you for your patience and understanding!

## Useful Links

- [GitHub Repository](https://github.com/CJFWeatherhead/ChatrixCD)
- [Issue Tracker](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- [Matrix.org](https://matrix.org/) - Learn about Matrix
- [Semaphore UI](https://github.com/ansible-semaphore/semaphore) - Learn about Semaphore UI
