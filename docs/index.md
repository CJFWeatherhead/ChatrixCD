---
layout: default
title: Home
nav_order: 1
---

<div align="center" style="margin: 2em 0;">
  <img src="assets/logo-horizontal.svg" alt="ChatrixCD Logo" width="500" style="max-width: 100%;">
</div>

<div align="center" style="margin: 2em 0;">
  <h1 style="font-size: 3em; margin-bottom: 0.5em;">🚀 ChatrixCD</h1>
  <p style="font-size: 1.3em; color: #4A9B7F;">Your CI/CD, Now in Chat! ✨</p>
  <p style="font-size: 1.1em; margin: 1em 0;">Matrix bot that brings Semaphore UI automation to your encrypted chat rooms</p>
</div>

<div align="center" style="margin: 2em 0;">
  <a href="installation.html" style="display: inline-block; padding: 15px 30px; background: #4A9B7F; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;">
    📥 Get Started
  </a>
  <a href="quickstart.html" style="display: inline-block; padding: 15px 30px; background: #2D3238; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;">
    ⚡ Quick Start
  </a>
  <a href="https://github.com/CJFWeatherhead/ChatrixCD" style="display: inline-block; padding: 15px 30px; background: #333; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;">
    🐙 GitHub
  </a>
</div>

---

## ✨ Why ChatrixCD?

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🔐 Secure by Default</h3>
  <p>End-to-end encryption support, OIDC/SSO authentication, and device verification built-in.</p>
</div>

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🎭 Fun & Friendly</h3>
  <p>Sassy bot personality with emoji, threaded responses, and reaction confirmations. Never boring!</p>
</div>

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🖥️ Interactive TUI</h3>
  <p>Beautiful terminal interface for monitoring, room management, and device verification.</p>
</div>

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🚀 CI/CD Made Easy</h3>
  <p>Start, monitor, and manage Semaphore tasks directly from chat with real-time updates.</p>
</div>

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🧠 Smart Automation</h3>
  <p>Auto-fill parameters, smart log tailing, custom aliases, and confirmation flows.</p>
</div>

<div style="padding: 20px; border: 2px solid #4A9B7F; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🎨 Rich Formatting</h3>
  <p>Colored status indicators, formatted logs, HTML tables, and semantic emoji throughout.</p>
</div>

</div>

---

## 🎯 Quick Start in 3 Steps

<div style="display: flex; flex-direction: column; gap: 20px; margin: 2em 0;">

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #4A9B7F; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #4A9B7F;">1️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Install ChatrixCD</h3>
    <p>Download the pre-built binary for Linux (no Python needed!) or install from source:</p>
    <pre><code>wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64
chmod +x chatrixcd-linux-x86_64</code></pre>
    <p><a href="installation.html">📖 Full Installation Guide →</a></p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #4A9B7F; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #4A9B7F;">2️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Configure Your Bot</h3>
    <p>Create a <code>config.json</code> with your Matrix and Semaphore details:</p>
    <pre><code>{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@your-bot:matrix.org",
    "auth_type": "password",
    "password": "your-password"
  },
  "semaphore": {
    "url": "https://semaphore.example.com",
    "api_token": "your-api-token"
  }
}</code></pre>
    <p><a href="configuration.html">⚙️ Configuration Guide →</a></p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #4A9B7F; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #4A9B7F;">3️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Start Automating!</h3>
    <p>Run the bot, invite it to your room, and start managing CI/CD tasks:</p>
    <pre><code>./chatrixcd-linux-x86_64

# In your Matrix room:
!cd projects
!cd run &lt;project_id&gt; &lt;template_id&gt;</code></pre>
    <p><a href="quickstart.html">⚡ Quick Start Guide →</a></p>
  </div>
</div>

</div>

---

## 🎨 Key Features

### 🔐 Security First
- **E2E Encryption**: Full support for encrypted Matrix rooms
- **Device Verification**: Emoji, QR code, and fingerprint verification
- **Native Auth**: Password and OIDC/SSO with Matrix homeservers
- **Secure Storage**: Encrypted credential storage

### 🎭 Delightful Experience
- **Threaded Responses**: Organized conversations with thread replies
- **Reaction Confirmations**: Quick 👍/👎 reactions for confirmations
- **Fun Personality**: Varied greetings, sassy responses, emoji everywhere
- **Rich Formatting**: Colored status, tables, formatted logs

### 🚀 Powerful Automation
- **Real-time Updates**: Automatic status updates for running tasks
- **Smart Parameters**: Auto-fill when only one option available
- **Command Aliases**: Custom shortcuts for frequent commands
- **Enhanced Logs**: Intelligent tailing for Ansible/Terraform

### 🖥️ Interactive TUI
- **Status Monitoring**: View bot status, connections, metrics
- **Room Management**: Manage Matrix rooms, invites, leaves
- **Device Verification**: Interactive verification flows
- **Log Viewing**: Real-time log streaming

---

## 📚 Documentation

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">📥 <a href="installation.html">Installation</a></h4>
  <p style="font-size: 0.9em;">Pre-built binaries, source, Docker</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">⚡ <a href="quickstart.html">Quick Start</a></h4>
  <p style="font-size: 0.9em;">Get up and running in minutes</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">⚙️ <a href="configuration.html">Configuration</a></h4>
  <p style="font-size: 0.9em;">Detailed config options</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🖥️ <a href="TUI.html">TUI Guide</a></h4>
  <p style="font-size: 0.9em;">Terminal interface features</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🏗️ <a href="architecture.html">Architecture</a></h4>
  <p style="font-size: 0.9em;">Technical design overview</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🚀 <a href="deployment.html">Deployment</a></h4>
  <p style="font-size: 0.9em;">Production deployment options</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🔒 <a href="security.html">Security</a></h4>
  <p style="font-size: 0.9em;">Security policy and best practices</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">🤝 <a href="contributing.html">Contributing</a></h4>
  <p style="font-size: 0.9em;">How to contribute to the project</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">❓ <a href="support.html">Support</a></h4>
  <p style="font-size: 0.9em;">Get help and troubleshooting</p>
</div>

</div>

---

## 🎯 Use Cases

<div style="margin: 2em 0;">

**💼 DevOps Teams**
- Trigger deployments from your team chat
- Monitor CI/CD pipelines in real-time
- Collaborate on deployment decisions with threaded discussions

**🚀 Rapid Response**
- Emergency deployments via mobile Matrix client
- Quick rollbacks when issues arise
- Status checks without leaving your chat

**🔐 Secure Ops**
- E2E encrypted deployment commands
- Audit trail of who triggered what
- OIDC/SSO integration with your identity provider

**🏢 Enterprise Ready**
- Self-hosted Matrix and Semaphore
- Role-based access with Matrix permissions
- Integrates with existing infrastructure

</div>

---

## 🌟 Getting Help

- 📖 **Documentation**: You're looking at it! Start with [Quick Start](quickstart.html)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/CJFWeatherhead/ChatrixCD/issues)
- 💬 **Questions**: Check [Support](support.html) or open a discussion
- 🤝 **Contributing**: See [Contributing Guide](contributing.html)

---

## 📜 License

ChatrixCD is open source under the **GNU General Public License v3.0**. See [LICENSE](https://github.com/CJFWeatherhead/ChatrixCD/blob/main/LICENSE) for details.

---

<div align="center" style="margin: 3em 0; padding: 2em; background: #f8f9fa; border-radius: 10px;">
  <h2 style="margin-top: 0;">Ready to automate? 🚀</h2>
  <p style="font-size: 1.1em;">Install ChatrixCD and start managing CI/CD from chat!</p>
  <a href="installation.html" style="display: inline-block; padding: 15px 40px; background: #4A9B7F; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin-top: 1em;">
    Get Started Now →
  </a>
</div>
