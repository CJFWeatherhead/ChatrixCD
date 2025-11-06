# Deployment Guide

This document provides an overview of deployment options for ChatrixCD.

## Quick Reference

| Method | Platform | Init System | File/Link |
|--------|----------|-------------|-----------|
| **Pre-built Binary** | Linux/Windows/macOS | systemd/manual | [Download](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest) |
| Docker | Debian-based | N/A | `Dockerfile` |
| Docker | Alpine Linux | N/A | `Dockerfile.alpine` |
| Native | Debian/Ubuntu | systemd | `chatrixcd-debian.service` |
| Native | RHEL/CentOS/Fedora | systemd | `chatrixcd.service` |
| Native | Alpine Linux | OpenRC | `chatrixcd.initd` |

## Recommended Deployments

### For Quick Deployment (Pre-built Binary)

**Best for:**
- Getting started quickly
- Simple deployments
- No Python installation needed
- Testing and evaluation

**Standalone executable:**
- **Statically compiled** with musl libc - no dependencies required
- Works on all Linux distributions (kernel 3.2+)
- Easy updates (just replace the binary)
- Smallest deployment footprint
- All libraries (OpenSSL, libffi, etc.) embedded in binary

**Download:** [Latest Release](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest)

See [INSTALL.md](INSTALL.md#method-1-pre-built-binary-recommended) for setup instructions.

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

| Feature | Pre-built Binary | Docker (Debian) | Docker (Alpine) | Native (Debian) | Native (Alpine) |
|---------|------------------|----------------|-----------------|-----------------|-----------------|
| Setup Time | Instant | Fast | Fast | Medium | Medium |
| Disk Usage | ~50-100MB | ~200MB | ~100MB | Minimal | Minimal |
| Memory Usage | Low | Medium | Low | Low | Very Low |
| Dependencies | None | Docker | Docker | Python + Deps | Python + Deps |
| Updates | Replace file | Rebuild image | Rebuild image | Update code | Update code |
| Security Hardening | Good | Good | Good | Excellent | Good |
| Ease of Deployment | Very Easy | Very Easy | Very Easy | Medium | Medium |
| Package Compatibility | Excellent | Excellent | Good | Excellent | Good |

## Choosing a Deployment Method

### Use Pre-built Binary if:
- You want the fastest setup
- You don't want to install Python
- You're testing or evaluating ChatrixCD
- You prefer simple file-based updates
- You're deploying on a single machine

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

## Detailed Instructions

For complete deployment instructions, see:

- [Pre-built Binary](INSTALL.md#method-1-pre-built-binary-recommended) - Quick start
- [Docker Deployment](INSTALL.md#method-3-docker-installation) - Containerized
- [Source Installation](INSTALL.md#method-2-install-from-source) - Development
- [Systemd Service](INSTALL.md#systemd-service-linux) - Native Linux service

## Security Considerations

All deployment methods include security best practices:

1. **Pre-built Binaries**: Statically linked, minimal attack surface
2. **Isolated User**: Bot runs as dedicated `chatrixcd` user (Docker/Native)
3. **Minimal Permissions**: Read-only filesystem where possible
4. **Protected Store**: Encryption keys stored with restricted access
5. **No New Privileges**: Security flags prevent privilege escalation
6. **Private Temp**: Isolated temporary directories

## Support

For issues or questions:
- Check [INSTALL.md](INSTALL.md) for detailed instructions
- Check [TROUBLESHOOTING.md](INSTALL.md#troubleshooting) section
- Open an issue on GitHub
