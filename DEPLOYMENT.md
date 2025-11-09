# Deployment Guide

This document provides an overview of deployment options for ChatrixCD.

## Quick Reference

| Method | Platform | Init System | File/Link |
|--------|----------|-------------|-----------|
| **Pre-built Binary** | Linux (Alpine-focused) | systemd/OpenRC/manual | [Download](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest) |
| Docker | **Alpine Linux (Primary)** | N/A | `Dockerfile.alpine` |
| Docker | Debian-based (Secondary) | N/A | `Dockerfile` |
| Native | **Alpine Linux (Primary)** | OpenRC | `chatrixcd.initd` |
| Native | Debian/Ubuntu (Secondary) | systemd | `chatrixcd-debian.service` |
| Native | RHEL/CentOS/Fedora (Secondary) | systemd | `chatrixcd.service` |

## Recommended Deployments

### For Quick Deployment (Pre-built Binary)

**Best for:**
- Getting started quickly
- Simple deployments
- No Python installation needed
- Testing and evaluation

**Standalone executable:**
- **Statically compiled** with musl libc targeting Alpine Linux 3.22+
- Works on all Linux distributions (kernel 3.2+)
- Easy updates (just replace the binary)
- Smallest deployment footprint
- All libraries (OpenSSL, libffi, etc.) embedded in binary
- Optimized for Alpine Linux but portable to other distributions

**Download:** [Latest Release](https://github.com/CJFWeatherhead/ChatrixCD/releases/latest)

See [INSTALL.md](INSTALL.md#method-1-pre-built-binary-recommended) for setup instructions.

### For Production (Docker)

**Alpine Linux (Primary - Recommended)**:
- Minimal deployments
- Smaller image size (~100MB)
- Faster builds
- Lower resource usage
- File: `Dockerfile.alpine`

**Debian-based (Secondary)**:
- Standard deployments
- Larger image size (~200MB)
- Better package compatibility for edge cases
- File: `Dockerfile`

### For Production (Native)

**Alpine Linux (Primary - Recommended)**:
- Minimal resource usage
- OpenRC init system
- Best alignment with project target
- File: `chatrixcd.initd`

**Debian/Ubuntu (Secondary)**:
- Enhanced security hardening
- Modern systemd features
- File: `chatrixcd-debian.service`

**RHEL/CentOS/Fedora (Secondary)**:
- Standard systemd configuration
- File: `chatrixcd.service`

## Feature Comparison

| Feature | Pre-built Binary | Docker (Alpine) | Docker (Debian) | Native (Alpine) | Native (Debian) |
|---------|------------------|-----------------|-----------------|-----------------|-----------------|
| Setup Time | Instant | Fast | Fast | Medium | Medium |
| Disk Usage | ~50-100MB | ~100MB | ~200MB | Minimal | Minimal |
| Memory Usage | Low | Low | Medium | Very Low | Low |
| Dependencies | None | Docker | Docker | Python + Deps | Python + Deps |
| Updates | Replace file | Rebuild image | Rebuild image | Update code | Update code |
| Security Hardening | Good | Good | Good | Good | Excellent |
| Ease of Deployment | Very Easy | Very Easy | Very Easy | Medium | Medium |
| Package Compatibility | Excellent | Good | Excellent | Good | Excellent |
| Target Alignment | ⭐ Primary | ⭐ Primary | Secondary | ⭐ Primary | Secondary |

## Choosing a Deployment Method

### Use Pre-built Binary if:
- You want the fastest setup
- You don't want to install Python
- You're testing or evaluating ChatrixCD
- You prefer simple file-based updates
- You're deploying on a single machine
- You're running Alpine Linux (primary target)

### Use Docker (Alpine) if:
- You want minimal resource usage (Primary recommendation)
- You prefer faster builds
- You need smaller images
- You want the best alignment with project targets

### Use Docker (Debian) if:
- You need maximum package compatibility for specific edge cases
- Image size is not a concern
- You're already using Debian-based infrastructure

### Use Native (Alpine) if:
- You need minimal system resources (Primary recommendation)
- You prefer OpenRC over systemd
- You're running Alpine Linux
- You want the best alignment with project targets

### Use Native (Debian) if:
- You want maximum security hardening with systemd
- You prefer native systemd integration
- You're on Debian/Ubuntu servers

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
