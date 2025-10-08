---
layout: default
title: Deployment
nav_order: 8
---

# Deployment Guide

Overview of deployment options for ChatrixCD.

## Quick Reference

| Platform | Method | Init System | File |
|----------|--------|-------------|------|
| Docker | Debian-based | N/A | `Dockerfile` |
| Docker | Alpine Linux | N/A | `Dockerfile.alpine` |
| Debian/Ubuntu | Native | systemd | `chatrixcd-debian.service` |
| RHEL/CentOS/Fedora | Native | systemd | `chatrixcd.service` |
| Alpine Linux | Native | OpenRC | `chatrixcd.initd` |

## Docker Deployment

### Debian-based (Recommended)

Best for standard deployments with maximum compatibility.

```bash
# Using Docker Compose
docker-compose up -d

# Or manually
docker build -t chatrixcd:latest .
docker run -d \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/store:/app/store \
  --name chatrixcd \
  chatrixcd:latest
```

**Pros:**
- Maximum package compatibility
- Well-tested base image
- Easy troubleshooting

**Cons:**
- Larger image size (~200MB)
- Slower builds

### Alpine Linux

Best for minimal deployments and resource efficiency.

```bash
# Using Docker Compose
docker-compose -f docker-compose.alpine.yml up -d

# Or manually
docker build -f Dockerfile.alpine -t chatrixcd:alpine .
docker run -d \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/store:/app/store \
  --name chatrixcd \
  chatrixcd:alpine
```

**Pros:**
- Smaller image size (~100MB)
- Faster builds
- Lower resource usage

**Cons:**
- Some packages may not be available
- Different system libraries (musl vs glibc)

## Native Deployment

### Debian/Ubuntu (systemd)

Enhanced security with modern systemd features.

```bash
# Install as service
sudo cp chatrixcd-debian.service /etc/systemd/system/chatrixcd.service
sudo systemctl daemon-reload
sudo systemctl enable chatrixcd
sudo systemctl start chatrixcd
```

**Features:**
- Enhanced security hardening
- Dynamic user creation
- Protected directories
- Automatic restart
- Resource limits

### RHEL/CentOS/Fedora (systemd)

Standard systemd configuration for Red Hat family.

```bash
# Install as service
sudo cp chatrixcd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatrixcd
sudo systemctl start chatrixcd
```

**Features:**
- Standard systemd configuration
- Service isolation
- Automatic restart
- Log management

### Alpine Linux (OpenRC)

Minimal deployment with OpenRC init system.

```bash
# Install as service
sudo cp chatrixcd.initd /etc/init.d/chatrixcd
sudo chmod +x /etc/init.d/chatrixcd
sudo rc-update add chatrixcd default
sudo rc-service chatrixcd start
```

**Features:**
- Minimal resource usage
- OpenRC init system
- Simple configuration
- Background operation

## Security Considerations

All deployment methods include security best practices:

1. **Isolated User**: Bot runs as dedicated user
2. **Minimal Permissions**: Read-only filesystem where possible
3. **Protected Store**: Encryption keys with restricted access
4. **No New Privileges**: Prevents privilege escalation
5. **Private Temp**: Isolated temporary directories

## Choosing a Deployment Method

### Use Docker (Debian) if:
- You want easiest deployment
- You need maximum compatibility
- Image size is not a concern

### Use Docker (Alpine) if:
- You want minimal resources
- You prefer faster builds
- You need smaller images

### Use Native (Debian) if:
- You want maximum security
- You prefer systemd integration
- You're on Debian/Ubuntu servers

### Use Native (Alpine) if:
- You need minimal resources
- You prefer OpenRC over systemd
- You're running Alpine Linux

## Monitoring

### Docker Logs

```bash
docker logs -f chatrixcd
docker-compose logs -f
```

### systemd Logs

```bash
sudo journalctl -u chatrixcd -f
sudo journalctl -u chatrixcd --since today
```

### OpenRC Logs

```bash
tail -f /var/log/chatrixcd.log
```

## Troubleshooting

### Service Won't Start

**Docker:**
```bash
docker logs chatrixcd
docker inspect chatrixcd
```

**systemd:**
```bash
sudo systemctl status chatrixcd
sudo journalctl -u chatrixcd -n 50
```

**OpenRC:**
```bash
sudo rc-service chatrixcd status
cat /var/log/chatrixcd.log
```

### Permission Issues

```bash
# Fix config permissions
chmod 600 config.yaml
chown chatrixcd:chatrixcd config.yaml

# Fix store permissions
chmod 700 store/
chown -R chatrixcd:chatrixcd store/
```

### Network Issues

```bash
# Test Matrix connectivity
curl -I https://your-matrix-server.com

# Test Semaphore connectivity
curl -I https://your-semaphore-server.com
```

## Updating

### Docker Update

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Restart container
docker-compose up -d
```

### Native Update

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart chatrixcd  # systemd
sudo rc-service chatrixcd restart # OpenRC
```

## Backup

### What to Backup

1. **Configuration**: `config.yaml` or `.env`
2. **Encryption Keys**: `store/` directory
3. **Service Files**: systemd/OpenRC configurations

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backup/chatrixcd/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup config
cp config.yaml "$BACKUP_DIR/"

# Backup store
cp -r store/ "$BACKUP_DIR/"

# Backup service file
cp /etc/systemd/system/chatrixcd.service "$BACKUP_DIR/"
```

## Related Documentation

- [Installation Guide](installation.html)
- [Configuration Guide](configuration.html)
- [Security Policy](security.html)
- [Support Guide](support.html)
