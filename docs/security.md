---
layout: single
title: Security
permalink: /security/
toc: true
toc_sticky: true
---

# Security Policy

For complete security guidelines, best practices, and detailed information, see the full [SECURITY.md](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/SECURITY.md) in the repository root.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅ Yes             |
| < Latest | ❌ No             |

We recommend always using the latest version.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Reporting Process

Report vulnerabilities via GitHub's private vulnerability reporting:

1. Go to the [Security tab](https://github.com/CJFWeatherhead/ChatrixCD/security)
2. Click "Report a vulnerability"
3. Fill in vulnerability details

### What to Include

- Type of vulnerability
- Full paths of affected source files
- Location of affected code (tag/branch/commit)
- Step-by-step reproduction instructions
- Proof-of-concept or exploit code (if possible)
- Impact assessment

### What to Expect

- Acknowledgment within 48 hours
- Regular updates on progress
- Credit in security advisory (if desired)
- Public disclosure timeline discussion

## Security Best Practices

### Credentials and Secrets

1. **Never commit credentials**
   - Don't commit `config.json` with real credentials
   - Use `.gitignore` to exclude sensitive files
   - Use secret management systems to generate config.json at deployment time

2. **Restrict file permissions**
   ```bash
   chmod 600 config.json
   chmod 700 store/
   ```

3. **Rotate credentials regularly**
   - Change bot passwords periodically
   - Regenerate API tokens regularly
   - Update access tokens when needed

### Encryption and Storage

1. **Secure the store directory**
   ```bash
   chmod 700 store/
   chown chatrixcd:chatrixcd store/
   ```

2. **Backup encryption keys**
   - Regularly backup `store/` directory
   - Store backups securely
   - Test restore procedures

3. **Enable E2E encryption**
   - Use encrypted Matrix rooms when possible
   - Verify device keys
   - Handle key backups properly

### Network Security

1. **Use HTTPS only**
   - Always use HTTPS for Matrix homeserver
   - Always use HTTPS for Semaphore API
   - Verify SSL certificates

2. **Network isolation**
   - Run bot in isolated network segment
   - Use firewall rules
   - Limit outbound connections

3. **API security**
   - Use least-privilege API tokens
   - Implement rate limiting (future)
   - Monitor API usage

### Access Control

1. **Restrict bot access**
   ```yaml
   bot:
     allowed_rooms:
       - "!secure-room:example.com"
   ```

2. **Review permissions**
   - Audit room memberships
   - Review bot capabilities
   - Monitor command usage

3. **User verification**
   - Verify users in sensitive rooms
   - Use room encryption
   - Implement user-based access control (future)

## Security Features

### Built-in Security

- ✅ E2E encryption support
- ✅ OIDC/OAuth2 authentication
- ✅ Secure token handling
- ✅ Access control mechanisms
- ✅ HTTPS-only endpoints

### Audit Logging

The bot logs security-relevant events:

- Authentication attempts
- Command executions
- Task operations
- Configuration errors

Review logs regularly:

```bash
grep -i "auth" /var/log/chatrixcd.log
grep -i "error" /var/log/chatrixcd.log
```

## Known Security Considerations

### Matrix Protocol

- Unencrypted rooms expose message content
- Device verification required for E2E
- Key backup security depends on passphrase

### Semaphore Integration

- API token has full Semaphore access
- Tasks run with Semaphore user permissions
- Task logs may contain sensitive data

### Bot Deployment

- Configuration files contain secrets
- Store directory contains encryption keys
- Process runs with configured user privileges

## Security Updates

Security updates are released ASAP after vulnerability confirmation.

### Update Notifications

Subscribe to:
- GitHub Security Advisories
- Repository notifications
- Release notifications

### Update Process

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart bot
systemctl restart chatrixcd
```

## Responsible Disclosure

We follow responsible disclosure practices:

1. Vulnerability reported privately
2. Issue confirmed and fixed
3. Security update released
4. Public disclosure with credit

We appreciate security researchers who:
- Report issues privately
- Allow time for fixes
- Follow responsible disclosure

## Security Checklist

### Deployment Security

- [ ] Configuration files protected (chmod 600)
- [ ] Store directory secured (chmod 700)
- [ ] Running as dedicated user
- [ ] Environment variables for secrets
- [ ] HTTPS for all endpoints
- [ ] Firewall rules configured
- [ ] Regular credential rotation
- [ ] Log monitoring enabled
- [ ] Backups secured
- [ ] Updates applied regularly

### Development Security

- [ ] No secrets in code
- [ ] No credentials in tests
- [ ] Dependencies regularly updated
- [ ] Security scanning enabled
- [ ] Code review required
- [ ] Test coverage maintained

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Matrix Security](https://matrix.org/docs/guides/matrix-security)
- [GitHub Security](https://docs.github.com/en/code-security)

## Contact

For security concerns:
- Use GitHub Security Advisories
- Contact repository maintainers
- Do not use public issues

Thank you for helping keep ChatrixCD secure! 🔒
