---
layout: default
title: Architecture
nav_order: 5
---

# 🏗️ Architecture

A visual guide to how ChatrixCD works under the hood.

<div style="padding: 15px; background: #e7f3ff; border-left: 4px solid #2196F3; margin: 1em 0;">
  <strong>💡 Quick Summary:</strong> ChatrixCD bridges Matrix (encrypted chat) and Semaphore UI (CI/CD automation) with a Python bot that handles commands, manages tasks, and provides a beautiful TUI.
</div>

---

## 📊 System Overview

<div align="center" style="margin: 2em 0;">
  <img src="assets/architecture-diagram.svg" alt="ChatrixCD Architecture Diagram" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;"/>
</div>

---

## 🧩 Core Components

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🤖 Bot Core (bot.py)</h3>
  <p><strong>The Heart of ChatrixCD</strong></p>
  <ul style="font-size: 0.9em;">
    <li>Matrix client management</li>
    <li>E2E encryption handling</li>
    <li>Event processing</li>
    <li>Auto-sync & device verification</li>
  </ul>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">⚡ Commands (commands.py)</h3>
  <p><strong>Command Processing Engine</strong></p>
  <ul style="font-size: 0.9em;">
    <li>Command parsing & validation</li>
    <li>Semaphore API integration</li>
    <li>Task management</li>
    <li>Response formatting</li>
  </ul>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🖥️ TUI (tui.py)</h3>
  <p><strong>Interactive Interface</strong></p>
  <ul style="font-size: 0.9em;">
    <li>Status monitoring</li>
    <li>Room management</li>
    <li>Device verification</li>
    <li>Log viewing</li>
  </ul>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">⚙️ Config (config.py)</h3>
  <p><strong>Configuration Manager</strong></p>
  <ul style="font-size: 0.9em;">
    <li>HJSON parsing</li>
    <li>Schema validation</li>
    <li>Auto-migration</li>
    <li>Secure defaults</li>
  </ul>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🚀 Semaphore (semaphore.py)</h3>
  <p><strong>CI/CD Integration</strong></p>
  <ul style="font-size: 0.9em;">
    <li>REST API client</li>
    <li>Task lifecycle management</li>
    <li>Status monitoring</li>
    <li>Log retrieval</li>
  </ul>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">📝 Messages (messages.py)</h3>
  <p><strong>Response Templates</strong></p>
  <ul style="font-size: 0.9em;">
    <li>Varied greetings</li>
    <li>Sassy responses</li>
    <li>Auto-reload support</li>
    <li>Emoji & formatting</li>
  </ul>
</div>

</div>

---

## 🔄 Data Flow

<div style="display: flex; flex-direction: column; gap: 20px; margin: 2em 0;">

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">1️⃣</div>
  <div>
    <h3 style="margin-top: 0;">User Sends Command</h3>
    <p>User types <code>!cd run 1 2</code> in a Matrix room</p>
    <p style="font-size: 0.9em; color: #666;">🔐 Message is E2E encrypted if room is encrypted</p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">2️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Bot Receives & Decrypts</h3>
    <p>Bot receives message event, decrypts it (if encrypted), and parses the command</p>
    <p style="font-size: 0.9em; color: #666;">🔍 Command parser validates syntax and permissions</p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">3️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Request Confirmation</h3>
    <p>Bot fetches template details and sends confirmation message with reaction buttons</p>
    <p style="font-size: 0.9em; color: #666;">👍👎 User reacts with thumbs up/down</p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">4️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Execute Task</h3>
    <p>Bot makes API call to Semaphore UI to start the task</p>
    <p style="font-size: 0.9em; color: #666;">🚀 Task ID returned and tracked</p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">5️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Monitor & Update</h3>
    <p>Bot polls task status and sends updates back to the room</p>
    <p style="font-size: 0.9em; color: #666;">📊 Real-time status updates with colored indicators</p>
  </div>
</div>

<div style="display: flex; align-items: start; padding: 20px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <div style="font-size: 2em; margin-right: 20px; min-width: 50px; text-align: center; font-weight: bold; color: #3e836b;">6️⃣</div>
  <div>
    <h3 style="margin-top: 0;">Task Complete</h3>
    <p>Final status sent with completion time and success/failure indicators</p>
    <p style="font-size: 0.9em; color: #666;">✅❌ Success = 🎉, Failure = 😔</p>
  </div>
</div>

</div>

---

## 🔐 Security Architecture

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🔒 E2E Encryption</h4>
  <p style="font-size: 0.9em;">Matrix-nio handles Olm/Megolm encryption automatically. All encrypted room messages are secure.</p>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🔑 Key Storage</h4>
  <p style="font-size: 0.9em;">Encryption keys stored in <code>store/</code> directory with proper file permissions.</p>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🛡️ Device Verification</h4>
  <p style="font-size: 0.9em;">Supports emoji, QR code, and fingerprint verification for trusted devices.</p>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🔐 OIDC/SSO</h4>
  <p style="font-size: 0.9em;">Native OIDC authentication with major identity providers.</p>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🚫 Permission Control</h4>
  <p style="font-size: 0.9em;">Configurable <code>allowed_rooms</code> restricts bot to authorized spaces.</p>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🔍 Audit Trail</h4>
  <p style="font-size: 0.9em;">All commands and actions logged for security auditing.</p>
</div>

</div>

---

## 🎯 Design Principles

<table style="width: 100%; border-collapse: collapse; margin: 2em 0;">
<thead style="background: #3e836b; color: white;">
<tr>
<th style="padding: 12px; text-align: left;">Principle</th>
<th style="padding: 12px; text-align: left;">Implementation</th>
</tr>
</thead>
<tbody>
<tr style="background: #f8f9fa;">
<td style="padding: 12px;"><strong>🔄 Async First</strong></td>
<td style="padding: 12px;">All I/O operations use async/await for non-blocking execution</td>
</tr>
<tr>
<td style="padding: 12px;"><strong>🎭 User Experience</strong></td>
<td style="padding: 12px;">Fun personality, emoji, reaction confirmations</td>
</tr>
<tr style="background: #f8f9fa;">
<td style="padding: 12px;"><strong>🛡️ Security First</strong></td>
<td style="padding: 12px;">E2E encryption, device verification, permission controls built-in</td>
</tr>
<tr>
<td style="padding: 12px;"><strong>🔧 Configuration</strong></td>
<td style="padding: 12px;">HJSON support, validation, auto-migration, sensible defaults</td>
</tr>
<tr style="background: #f8f9fa;">
<td style="padding: 12px;"><strong>📝 DRY Code</strong></td>
<td style="padding: 12px;">Extracted helpers, shared utilities, reusable components</td>
</tr>
<tr>
<td style="padding: 12px;"><strong>✅ Testability</strong></td>
<td style="padding: 12px;">Small focused methods, dependency injection, comprehensive tests</td>
</tr>
</tbody>
</table>

---

## 📦 Technology Stack

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🐍 Python 3.12+</h4>
  <p style="font-size: 0.9em;">Modern Python with async/await</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">📱 matrix-nio</h4>
  <p style="font-size: 0.9em;">Matrix client with E2E encryption</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🌐 aiohttp</h4>
  <p style="font-size: 0.9em;">Async HTTP for Semaphore API</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🖥️ Textual</h4>
  <p style="font-size: 0.9em;">Terminal UI framework</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">📝 HJSON</h4>
  <p style="font-size: 0.9em;">Human-friendly JSON config</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <h4 style="margin-top: 0;">🔐 cryptography</h4>
  <p style="font-size: 0.9em;">Encryption & key management</p>
</div>

</div>

---

## 📚 Learn More

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>🔧 Implementation Details</strong>
  <p style="font-size: 0.9em;"><a href="https://github.com/CJFWeatherhead/ChatrixCD/blob/main/ARCHITECTURE.md">Full ARCHITECTURE.md →</a></p>
</div>

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>🤝 Contributing</strong>
  <p style="font-size: 0.9em;"><a href="contributing.html">Contributing Guide →</a></p>
</div>

<div style="padding: 15px; border-left: 4px solid #3e836b; background: #f8f9fa;">
  <strong>🔒 Security</strong>
  <p style="font-size: 0.9em;"><a href="security.html">Security Policy →</a></p>
</div>

</div>
