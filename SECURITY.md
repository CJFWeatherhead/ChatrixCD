# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the project's maturity:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest | :x:                |

As this project is in early development, we recommend always using the latest version.

## Reporting a Vulnerability

We take the security of ChatrixCD seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Reporting Process

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://github.com/CJFWeatherhead/ChatrixCD/security) of this repository
2. Click "Report a vulnerability"
3. Fill in the details of the vulnerability

Alternatively, you can email the repository owner directly. Please include:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Disclosure**: Once the vulnerability is fixed, we will publicly disclose it (with credit to you, if desired)
- **Timeline**: We aim to resolve critical vulnerabilities within 7 days

## Security Best Practices for Users

When deploying ChatrixCD, follow these security best practices:

### Credentials and Secrets

1. **Never commit credentials**: Don't commit `config.json` or `.env` files with real credentials to version control
2. **Use environment variables**: Prefer environment variables for production deployments
3. **Restrict file permissions**: Ensure configuration files are readable only by the bot user
   ```bash
   chmod 600 config.json
   chmod 600 .env
   ```
4. **Rotate credentials regularly**: Change bot passwords and API tokens periodically

### Encryption and Storage

1. **Secure the store directory**: The `store/` directory contains encryption keys - protect it with appropriate permissions
   ```bash
   chmod 700 store/
   ```
2. **Backup encryption keys**: Regularly backup the `store/` directory securely
3. **Enable E2E encryption**: Use end-to-end encrypted Matrix rooms when possible

### Access Control

1. **Use room allowlists**: Configure `allowed_rooms` to restrict which rooms the bot joins
2. **Limit admin users**: Only grant admin privileges to trusted users via `admin_users`
3. **Minimal API permissions**: Create Semaphore API tokens with only the permissions needed
4. **Network segmentation**: Run the bot in a restricted network environment if possible

### Network Security

1. **Use HTTPS**: Always use HTTPS endpoints for Matrix homeserver and Semaphore UI
2. **Verify certificates**: Ensure SSL/TLS certificates are properly validated
3. **Firewall rules**: Configure firewalls to allow only necessary outbound connections

### Monitoring and Updates

1. **Regular updates**: Keep dependencies updated to receive security patches
   ```bash
   uv pip install -r requirements.txt --upgrade
   ```
2. **Monitor logs**: Set up logging and regularly review logs for suspicious activity
3. **Security scanning**: Regularly scan for vulnerabilities in dependencies
4. **Subscribe to security advisories**: Watch this repository for security updates

### Deployment Security

#### Docker Deployments

1. **Run as non-root**: The Docker image should run as a non-root user
2. **Read-only root filesystem**: Use `--read-only` flag when possible
3. **Drop capabilities**: Drop unnecessary Linux capabilities
4. **Scan images**: Regularly scan Docker images for vulnerabilities

#### Systemd Deployments

1. **Dedicated user**: Run the bot as a dedicated, non-privileged user
2. **Service hardening**: Use systemd security features (NoNewPrivileges, PrivateTmp, etc.)
3. **Resource limits**: Set appropriate resource limits in the service file

## Known Security Considerations

### Encryption Keys

- **Critical**: The bot stores Matrix E2E encryption keys in the `store_path` directory
- **Risk**: Loss of this directory means loss of access to encrypted message history
- **Mitigation**: Regular backups, proper file permissions, and secure storage

### API Tokens

- **Critical**: Semaphore API tokens provide access to your CI/CD infrastructure
- **Risk**: Compromised tokens could allow unauthorized task execution
- **Mitigation**: Use tokens with minimal permissions, rotate regularly, monitor usage

### Bot Permissions

- **Critical**: The bot has the permissions of its Matrix account
- **Risk**: A compromised bot could send messages or access rooms it has joined
- **Mitigation**: Use `allowed_rooms` to restrict access, monitor bot activity

### Memory Storage

- **Note**: Task tracking is stored in memory only
- **Risk**: Task state is lost on bot restart
- **Mitigation**: This is by design; sensitive task data is not persisted

## Security Features

### Built-in Security

- **E2E Encryption Support**: Full support for encrypted Matrix rooms via matrix-nio
- **OIDC Authentication**: Secure OAuth2/OIDC authentication with Matrix homeservers
- **Token Security**: Authentication tokens are never logged and stored in memory only
- **Access Control**: Room and user-based access control mechanisms
- **Secure Defaults**: HTTPS-only endpoints, secure token handling

### Audit Logging

The bot logs the following security-relevant events:

- Authentication attempts
- Command executions with user and room information
- Task start/stop operations
- Configuration errors

Review logs regularly for suspicious activity.

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed and fixed. Updates will be announced through:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Git tags and GitHub releases

Subscribe to repository notifications to stay informed about security updates.

## Responsible Disclosure

We appreciate responsible disclosure of security vulnerabilities. We will:

- Acknowledge your contribution in the security advisory (if desired)
- Keep you informed of the remediation progress
- Credit you in release notes (if desired)

Thank you for helping keep ChatrixCD and its users safe!
