---
layout: default
title: Installation
nav_order: 2
---

# 📥 Installation Guide

Choose the installation method that works best for you!

---

## 🎯 Quick Comparison

<table style="width: 100%; border-collapse: collapse; margin: 2em 0;">
<thead style="background: #3e836b; color: white;">
<tr>
<th style="padding: 12px; text-align: left;">Method</th>
<th style="padding: 12px; text-align: center;">Difficulty</th>
<th style="padding: 12px; text-align: center;">Requirements</th>
<th style="padding: 12px; text-align: left;">Best For</th>
</tr>
</thead>
<tbody>
<tr style="background: #f8f9fa;">
<td style="padding: 12px;"><strong>�� Pre-built Binary</strong></td>
<td style="padding: 12px; text-align: center;">⭐ Easy</td>
<td style="padding: 12px; text-align: center;">None!</td>
<td style="padding: 12px;">Linux users, quick setup</td>
</tr>
<tr>
<td style="padding: 12px;"><strong>🔧 From Source</strong></td>
<td style="padding: 12px; text-align: center;">⭐⭐ Medium</td>
<td style="padding: 12px; text-align: center;">Python 3.12+</td>
<td style="padding: 12px;">Development, Windows/macOS</td>
</tr>
<tr style="background: #f8f9fa;">
<td style="padding: 12px;"><strong>🐳 Docker</strong></td>
<td style="padding: 12px; text-align: center;">⭐⭐ Medium</td>
<td style="padding: 12px; text-align: center;">Docker</td>
<td style="padding: 12px;">Containerized deployments</td>
</tr>
</tbody>
</table>

---

## Method 1: 📦 Pre-built Binary (Recommended)

<div style="padding: 20px; background: #e8f5e9; border-left: 4px solid #4caf50; margin: 1em 0;">
  <strong>✅ Easiest option!</strong> No Python installation required. Fully static binaries with zero dependencies.
</div>

### Why Pre-built Binaries?

- 🚀 **Zero Dependencies** - No glibc, OpenSSL, Python, or system libraries needed
- 🔒 **Maximum Portability** - Works on any Linux distro (kernel 3.2+)
- 📦 **Self-Contained** - Everything bundled in one file
- ⚡ **Fast** - Optimized builds with musl libc

### Download Links

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">💻 x86_64 (64-bit)</h4>
  <p><strong>Most common</strong></p>
  <p>Intel/AMD 64-bit processors</p>
  <a href="https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz" style="display: inline-block; padding: 10px 20px; background: #3e836b; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Download →</a>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🖥️ i686 (32-bit)</h4>
  <p><strong>Older systems</strong></p>
  <p>32-bit Intel/AMD processors</p>
  <a href="https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-i686.dist.tar.gz" style="display: inline-block; padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Download →</a>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🥧 ARM64</h4>
  <p><strong>ARM devices</strong></p>
  <p>Raspberry Pi, ARM servers</p>
  <a href="https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-arm64.dist.tar.gz" style="display: inline-block; padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">Download →</a>
</div>

</div>

### Installation Steps

```bash
# 1. Download (example for x86_64)
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz

# 2. Extract
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist

# 3. Run it!
./chatrixcd
```

<div style="padding: 15px; background: #e7f3ff; border-left: 4px solid #2196F3; margin: 1em 0;">
  <strong>💡 Pro Tip:</strong> Move the binary to <code>/usr/local/bin/chatrixcd</code> to run it from anywhere!
</div>

---

## Method 2: 🔧 From Source

Perfect for development, customization, or if binaries aren't available for your platform.

### Prerequisites

- Python 3.12, 3.13, or 3.14
- pip (Python package manager)
- git

<details style="margin: 1em 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
<summary style="cursor: pointer; font-weight: bold;">📋 Platform-Specific Prerequisites (Click to expand)</summary>

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**macOS (with Homebrew):**
```bash
brew install python@3.12 git
```

**Windows:**
1. Install [Python 3.12+](https://www.python.org/downloads/)
2. Install [Git for Windows](https://git-scm.com/download/win)
</details>

### Installation Steps

<div style="display: flex; flex-direction: column; gap: 15px; margin: 2em 0;">

<div style="display: flex; align-items: start; padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px; text-align: center;">1️⃣</div>
  <div style="flex: 1;">
    <strong>Clone the Repository</strong>
    <pre><code>git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD</code></pre>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px; text-align: center;">2️⃣</div>
  <div style="flex: 1;">
    <strong>Create Virtual Environment</strong>
    <pre><code>python -m venv .venv</code></pre>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px; text-align: center;">3️⃣</div>
  <div style="flex: 1;">
    <strong>Activate Virtual Environment</strong>
    <pre><code># Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate</code></pre>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px; text-align: center;">4️⃣</div>
  <div style="flex: 1;">
    <strong>Install Dependencies</strong>
    <pre><code>pip install -r requirements.txt
pip install -e .</code></pre>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px; text-align: center;">5️⃣</div>
  <div style="flex: 1;">
    <strong>Run ChatrixCD</strong>
    <pre><code>chatrixcd</code></pre>
  </div>
</div>

</div>

---

## Method 3: 🐳 Docker

Perfect for containerized deployments and production environments.

### Quick Start

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or using docker run
docker run -d \
  --name chatrixcd \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/store:/app/store \
  ghcr.io/cjfweatherhead/chatrixcd:latest
```

### Dockerfile

```dockerfile
FROM python:3.12-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN pip install -e .

# Run
CMD ["chatrixcd"]
```

<div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 1em 0;">
  <strong>⚠️ Remember:</strong> Mount your <code>config.json</code> and <code>store/</code> directory as volumes!
</div>

---

## 🪟 Windows & 🍎 macOS Users

Pre-built binaries aren't available yet for Windows and macOS. Choose one of these options:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">✅ From Source</h3>
  <p><strong>Recommended</strong></p>
  <p>Native installation with full TUI support</p>
  <a href="#method-2--from-source">See Method 2 →</a>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px;">
  <h3 style="margin-top: 0;">🐳 Docker Desktop</h3>
  <p><strong>Containerized</strong></p>
  <p>Works on both platforms</p>
  <a href="#method-3--docker">See Method 3 →</a>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px;">
  <h3 style="margin-top: 0;">🪟 WSL2 (Windows Only)</h3>
  <p><strong>Linux on Windows</strong></p>
  <p>Use Linux binaries on Windows</p>
  <details style="margin-top: 10px;">
  <summary style="cursor: pointer;">View instructions</summary>
  <pre><code># Install WSL2
wsl --install

# In WSL terminal:
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist
./chatrixcd</code></pre>
  </details>
</div>

</div>

---

## ⚙️ Post-Installation

After installing, you need to:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>1️⃣ Create config.json</strong>
  <p style="font-size: 0.9em;"><a href="configuration.html">Configuration Guide →</a></p>
</div>

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>2️⃣ Run ChatrixCD</strong>
  <p style="font-size: 0.9em;"><a href="quickstart.html">Quick Start Guide →</a></p>
</div>

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>3️⃣ Invite to Room</strong>
  <p style="font-size: 0.9em;"><a href="quickstart.html#step-4%EF%B8%8F%E2%83%A3-invite-bot-to-your-room">Invitation Steps →</a></p>
</div>

</div>

---

## 🚀 Production Deployment

For production use, consider:

- **systemd Service**: Auto-start on boot ([Deployment Guide](deployment.html))
- **Docker**: Containerized deployment ([Method 3](#method-3--docker))
- **Monitoring**: Set up health checks and logging
- **Security**: Use OIDC/SSO, restrict allowed_rooms

<a href="deployment.html" style="display: inline-block; padding: 15px 30px; background: #3e836b; color: white; text-decoration: none; border-radius: 8px; margin: 2em 0;">
  📖 Full Deployment Guide →
</a>

---

## ❓ Need Help?

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🐛 Issues?</h4>
  <p style="font-size: 0.9em;"><a href="https://github.com/CJFWeatherhead/ChatrixCD/issues">Report on GitHub</a></p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">📖 Docs</h4>
  <p style="font-size: 0.9em;"><a href="support.html">Support Guide</a></p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">💬 Questions?</h4>
  <p style="font-size: 0.9em;"><a href="https://github.com/CJFWeatherhead/ChatrixCD/discussions">GitHub Discussions</a></p>
</div>

</div>
