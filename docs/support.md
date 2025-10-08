---
layout: default
title: Support
nav_order: 9
---

# Support Guide

Get help with ChatrixCD.

## Getting Help

### Documentation

Start with our documentation:
- [Installation Guide](installation.html)
- [Quick Start](quickstart.html)
- [Configuration Guide](configuration.html)
- [Architecture Overview](architecture.html)

### GitHub Resources

- [GitHub Issues](https://github.com/CJFWeatherhead/ChatrixCD/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/CJFWeatherhead/ChatrixCD/discussions) - Questions and community support
- [GitHub Wiki](https://github.com/CJFWeatherhead/ChatrixCD/wiki) - Additional resources

## Common Issues

### Installation Problems

#### Dependencies Won't Install

```bash
# Upgrade pip
pip install --upgrade pip

# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt
```

#### Python Version Issues

```bash
# Check Python version (need 3.8+)
python --version

# Use specific Python version
python3.11 -m venv .venv
```

### Configuration Issues

#### Bot Won't Start

1. **Check configuration file**
   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Check environment variables**
   ```bash
   # List environment variables
   env | grep -E "(MATRIX|SEMAPHORE|BOT)_"
   ```

3. **Check file permissions**
   ```bash
   ls -la config.yaml
   ls -la store/
   ```

#### Authentication Fails

**Password Authentication:**
```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  password: "your-password"
  auth_type: "password"  # Ensure this is set
```

**Token Authentication:**
```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  access_token: "your-token"
  auth_type: "token"
```

**OIDC Authentication:**
```yaml
matrix:
  homeserver: "https://matrix.example.com"
  user_id: "@bot:example.com"
  auth_type: "oidc"
  oidc:
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    issuer: "https://auth.example.com"
```

### Runtime Issues

#### Bot Doesn't Respond

1. **Check bot joined room**
   - Look for join confirmation in logs
   - Re-invite bot if needed: `/invite @bot:example.com`

2. **Check allowed rooms**
   ```yaml
   bot:
     allowed_rooms: []  # Empty = all rooms allowed
   ```

3. **Check command prefix**
   ```yaml
   bot:
     command_prefix: "!cd"  # Must match what you're typing
   ```

4. **Check logs**
   ```bash
   # Docker
   docker logs -f chatrixcd
   
   # systemd
   sudo journalctl -u chatrixcd -f
   ```

#### Semaphore Integration Issues

1. **Test Semaphore API**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://semaphore.example.com/api/projects
   ```

2. **Verify API token**
   - Check token is valid
   - Verify token has correct permissions
   - Regenerate token if needed

3. **Check URL format**
   ```yaml
   semaphore:
     url: "https://semaphore.example.com"  # No trailing slash
   ```

#### Encryption Issues

1. **Verify device**
   - Check Matrix client for unverified devices
   - Verify bot device in Element/other client

2. **Reset encryption**
   ```bash
   # Backup first!
   mv store/ store.backup/
   mkdir store/
   # Restart bot to generate new keys
   ```

3. **Check store permissions**
   ```bash
   chmod 700 store/
   ls -la store/
   ```

### Performance Issues

#### High Memory Usage

1. **Check room count**
   - Bot joins all invited rooms by default
   - Use `allowed_rooms` to limit

2. **Monitor sync size**
   - Large sync responses increase memory
   - Consider smaller room history

3. **Restart periodically**
   ```bash
   # systemd auto-restart on failure
   sudo systemctl restart chatrixcd
   ```

#### Slow Response Times

1. **Check network latency**
   ```bash
   ping matrix.example.com
   curl -w "@curl-format.txt" https://matrix.example.com
   ```

2. **Check API response times**
   ```bash
   time curl https://semaphore.example.com/api/projects
   ```

3. **Review logs for errors**
   ```bash
   grep -i "error\|timeout" /var/log/chatrixcd.log
   ```

## Debugging

### Enable Debug Logging

Edit configuration or environment:

```yaml
logging:
  level: "DEBUG"
```

Or:
```bash
export LOG_LEVEL="DEBUG"
```

### Collect Debug Information

When reporting issues, include:

1. **Version information**
   ```bash
   chatrixcd --version
   python --version
   pip list
   ```

2. **Configuration** (remove secrets!)
   ```bash
   cat config.yaml | sed 's/password:.*/password: REDACTED/'
   ```

3. **Logs**
   ```bash
   # Last 100 lines
   journalctl -u chatrixcd -n 100
   ```

4. **System information**
   ```bash
   uname -a
   cat /etc/os-release
   ```

## Reporting Bugs

When reporting bugs on GitHub:

1. **Search existing issues** first
2. **Use the bug report template**
3. **Include debug information** (see above)
4. **Describe steps to reproduce**
5. **Remove sensitive data** (passwords, tokens, etc.)

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.2]
- ChatrixCD: [e.g., 2024.12.0]
- Deployment: [e.g., Docker, systemd]

**Logs**
```
Relevant log output (with secrets removed)
```
```

## Feature Requests

When requesting features:

1. **Check existing requests** first
2. **Use the feature request template**
3. **Describe the use case**
4. **Suggest implementation** (optional)

## Community Support

### Best Practices

- Be respectful and patient
- Provide complete information
- Follow up on responses
- Share solutions you find

### Getting Faster Help

- Use clear, descriptive titles
- Include relevant details upfront
- Format code and logs properly
- Test suggestions and report results

## Professional Support

For professional support needs:
- Contact repository maintainers
- Consider sponsoring the project
- Contribute to development

## Additional Resources

- [Matrix Protocol Docs](https://matrix.org/docs/)
- [matrix-nio Documentation](https://matrix-nio.readthedocs.io/)
- [Semaphore UI Docs](https://docs.ansible-semaphore.com/)
- [Python asyncio Docs](https://docs.python.org/3/library/asyncio.html)

## Contributing Back

Found a solution? Help others by:
- Updating documentation
- Creating a wiki page
- Answering questions in discussions
- Contributing code fixes

See [Contributing Guide](contributing.html) for more information.

Thank you for using ChatrixCD! 🙏
