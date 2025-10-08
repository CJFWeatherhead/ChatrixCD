# Deployment Guide

This document provides an overview of deployment options for ChatrixCD.

## Quick Reference

| Platform | Method | Init System | File |
|----------|--------|-------------|------|
| Docker | Debian-based | N/A | `Dockerfile` |
| Docker | Alpine Linux | N/A | `Dockerfile.alpine` |
| Debian/Ubuntu | Native | systemd | `chatrixcd-debian.service` |
| RHEL/CentOS/Fedora | Native | systemd | `chatrixcd.service` |
| Alpine Linux | Native | OpenRC | `chatrixcd.initd` |

## Recommended Deployments

### For Production (Docker)

**Debian-based** (default):
- Use for standard deployments
- Larger image size (~200MB)
- Better package compatibility
- File: `Dockerfile`

**Alpine Linux**:
- Use for minimal deployments
- Smaller image size (~100MB)
- Faster builds
- File: `Dockerfile.alpine`

### For Production (Native)

**Debian/Ubuntu**:
- Enhanced security hardening
- Modern systemd features
- File: `chatrixcd-debian.service`

**RHEL/CentOS/Fedora**:
- Standard systemd configuration
- File: `chatrixcd.service`

**Alpine Linux**:
- Minimal resource usage
- OpenRC init system
- File: `chatrixcd.initd`

## Feature Comparison

| Feature | Docker (Debian) | Docker (Alpine) | Native (Debian) | Native (Alpine) |
|---------|----------------|-----------------|-----------------|-----------------|
| Image Size | ~200MB | ~100MB | N/A | N/A |
| Build Time | Medium | Fast | N/A | N/A |
| Memory Usage | Medium | Low | Low | Very Low |
| Security Hardening | Good | Good | Excellent | Good |
| Ease of Deployment | Very Easy | Very Easy | Medium | Medium |
| Package Compatibility | Excellent | Good | Excellent | Good |

## Detailed Instructions

For complete deployment instructions, see [INSTALL.md](INSTALL.md):

- [Docker Deployment](INSTALL.md#docker-deployment)
- [Debian-Specific Deployment](INSTALL.md#debian-specific-deployment)
- [Alpine Linux Deployment](INSTALL.md#alpine-linux-deployment)
- [Systemd Service](INSTALL.md#systemd-service-linux)

## Security Considerations

All deployment methods include security best practices:

1. **Isolated User**: Bot runs as dedicated `chatrixcd` user
2. **Minimal Permissions**: Read-only filesystem where possible
3. **Protected Store**: Encryption keys stored with restricted access
4. **No New Privileges**: Security flags prevent privilege escalation
5. **Private Temp**: Isolated temporary directories

## Choosing a Deployment Method

### Use Docker (Debian) if:
- You want the easiest deployment
- You need maximum package compatibility
- Image size is not a concern

### Use Docker (Alpine) if:
- You want minimal resource usage
- You prefer faster builds
- You need smaller images

### Use Native (Debian) if:
- You want maximum security hardening
- You prefer native systemd integration
- You're on Debian/Ubuntu servers

### Use Native (Alpine) if:
- You need minimal system resources
- You prefer OpenRC over systemd
- You're running Alpine Linux

## Support

For issues or questions:
- Check [INSTALL.md](INSTALL.md) for detailed instructions
- Check [TROUBLESHOOTING.md](INSTALL.md#troubleshooting) section
- Open an issue on GitHub
