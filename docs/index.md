---
layout: default
title: Home
nav_order: 1
---

<div align="center" style="margin: 2em 0;">
  <img src="assets/logo-horizontal.svg" alt="ChatrixCD - Matrix bot for CI/CD automation" width="500" style="max-width: 100%;">
</div>

<header id="main-content" role="banner">
  <div align="center" style="margin: 2em 0;">
    <!--- <h1 style="font-size: 3em; margin-bottom: 0.5em;">🚀 ChatrixCD</h1> --->
    <p style="font-size: 1.3em; color: #3e836b;">Your CI/CD, Now in Chat! ✨</p>
    <p style="font-size: 1.1em; margin: 1em 0;">Matrix bot that brings Semaphore UI automation to your encrypted chat rooms</p>
  </div>
</header>

<nav role="navigation" aria-label="Quick access navigation">
  <div align="center" style="margin: 2em 0;">
    <a href="download.html" style="display: inline-block; padding: 15px 30px; background: #3e836b; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;" aria-label="Get Started with Download">
      📥 Get Started
    </a>
    <a href="quickstart.html" style="display: inline-block; padding: 15px 30px; background: #2D3238; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;" aria-label="View Quick Start Guide">
      ⚡ Quick Start
    </a>
    <a href="https://github.com/CJFWeatherhead/ChatrixCD" style="display: inline-block; padding: 15px 30px; background: #333; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin: 10px;" aria-label="View ChatrixCD on GitHub" rel="noopener noreferrer" target="_blank">
      🐙 GitHub
    </a>
  </div>
</nav>

---

## ✨ Why ChatrixCD?

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 2em 0;" role="list">

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🔐 Secure by Default</h3>
  <p>End-to-end encryption support, OIDC/SSO authentication, and device verification built-in.</p>
</article>

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🎭 Fun & Friendly</h3>
  <p>Sassy bot personality with emoji, and reaction confirmations. Never boring!</p>
</article>

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🖥️ Interactive TUI</h3>
  <p>Beautiful terminal interface for monitoring, room management, and device verification.</p>
</article>

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🚀 CI/CD Made Easy</h3>
  <p>Start, monitor, and manage Semaphore tasks directly from chat with real-time updates.</p>
</article>

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🧠 Smart Automation</h3>
  <p>Auto-fill parameters, smart log tailing, custom aliases, and confirmation flows.</p>
</article>

<article style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;" role="listitem">
  <h3 style="margin-top: 0;">🎨 Rich Formatting</h3>
  <p>Colored status indicators, formatted logs, HTML tables, and semantic emoji throughout.</p>
</article>

</div>

---

## 🎯 Quick Start in 2 Steps

<ol style="list-style: none; padding: 0; margin: 2em 0;">

<li style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; margin-bottom: 20px;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;" aria-hidden="true">1️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Download & Run ChatrixCD</h3>
    <p>Download the pre-built binary for Linux (no Python needed!) or install from source:</p>
    <pre><code>wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist
./chatrixcd</code></pre>
    <p><a href="download.html">📖 Download Page →</a></p>
  </div>
</li>

<li style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;" aria-hidden="true">2️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Start Automating!</h3>
    <p>The bot will guide you through configuration. Invite it to your room and start managing CI/CD tasks:</p>
    <pre><code># In your Matrix room:
!cd projects
!cd run &lt;project_id&gt; &lt;template_id&gt;</code></pre>
    <p><a href="quickstart.html">⚡ Quick Start Guide →</a></p>
  </div>
</li>

</ol>

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
  - Add: `!cd aliases add <alias> <command>` (prefixed or unprefixed)
  - Remove: `!cd aliases remove <alias>`
  - Aliases preserve extra flags/args when invoked
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
  <h4 style="margin-top: 0;">📥 <a href="download.html">Download</a></h4>
  <p style="font-size: 0.9em;">Pre-built binaries for Linux</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <h4 style="margin-top: 0;">📥 <a href="installation.html">Installation</a></h4>
  <p style="font-size: 0.9em;">From source, Docker, advanced options</p>
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

<h3>💼 DevOps Teams</h3>
<ul>
  <li>Trigger deployments from your team chat</li>
  <li>Monitor CI/CD pipelines in real-time</li>
  <li>Collaborate on deployment decisions with threaded discussions</li>
</ul>

<h3>🚀 Rapid Response</h3>
<ul>
  <li>Emergency deployments via mobile Matrix client</li>
  <li>Quick rollbacks when issues arise</li>
  <li>Status checks without leaving your chat</li>
</ul>

<h3>🔐 Secure Ops</h3>
<ul>
  <li>E2E encrypted deployment commands</li>
  <li>Audit trail of who triggered what</li>
  <li>OIDC/SSO integration with your identity provider</li>
</ul>

<h3>🏢 Enterprise Ready</h3>
<ul>
  <li>Self-hosted Matrix and Semaphore</li>
  <li>Role-based access with Matrix permissions</li>
  <li>Integrates with existing infrastructure</li>
</ul>


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

<section style="margin: 3em 0; padding: 2em; border-radius: 10px; text-align: center;" role="region" aria-label="Call to action">
  <h2 style="margin-top: 0;">Ready to automate? 🚀</h2>
  <p style="font-size: 1.1em;">Install ChatrixCD and start managing CI/CD from chat!</p>
  <a href="installation.html" style="display: inline-block; padding: 15px 40px; background: #3e836b; color: white; text-decoration: none; border-radius: 8px; font-size: 1.2em; margin-top: 1em;" aria-label="Get started with ChatrixCD installation">
    Get Started Now →
  </a>
</section>
