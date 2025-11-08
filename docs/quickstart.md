---
layout: default
title: Quick Start
nav_order: 3
---

# ⚡ Quick Start Guide

Get ChatrixCD up and running in **5 minutes**! 🚀

<div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 1em 0;">
  <strong>⏱️ Time to Success:</strong> ~5 minutes<br>
  <strong>📋 What You'll Need:</strong> Matrix account, Semaphore UI access<br>
  <strong>�� What You'll Get:</strong> Fully working CI/CD bot in your chat!
</div>

---

## Step 1️⃣: Install ChatrixCD

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">📦 Pre-built Binary (Easiest!)</h3>
  <p><strong>✅ Recommended for most users</strong></p>
  <p>No Python required! Just download and run:</p>
  <pre><code>wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64
chmod +x chatrixcd-linux-x86_64
./chatrixcd-linux-x86_64</code></pre>
  <p><small>📖 <a href="installation.html#method-1-pre-built-binary-recommended">More download options →</a></small></p>
</div>

<div style="padding: 20px; border: 2px solid #6c757d; border-radius: 10px; background: #f8f9fa;">
  <h3 style="margin-top: 0;">🔧 From Source (Advanced)</h3>
  <p><strong>For development or customization</strong></p>
  <pre><code>git clone https://github.com/CJFWeatherhead/ChatrixCD.git
cd ChatrixCD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .</code></pre>
  <p><small>📖 <a href="installation.html#method-2-from-source">Full source guide →</a></small></p>
</div>

</div>

---

## Step 2️⃣: Create Configuration

Create a `config.json` file in the same directory:

<div style="padding: 15px; background: #e7f3ff; border-left: 4px solid #2196F3; margin: 1em 0;">
  <strong>💡 Tip:</strong> Start with password auth for simplicity. You can switch to OIDC/SSO later!
</div>

```json
{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@your-bot:matrix.org",
    "auth_type": "password",
    "password": "your-secure-password"
  },
  "semaphore": {
    "url": "https://your-semaphore.example.com",
    "api_token": "your-api-token-here"
  },
  "bot": {
    "command_prefix": "!cd",
    "allowed_rooms": []
  }
}
```

<details style="margin: 1em 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
<summary style="cursor: pointer; font-weight: bold;">🔐 Using OIDC/SSO instead? (Click to expand)</summary>
<pre><code>{
  "matrix": {
    "homeserver": "https://matrix.org",
    "user_id": "@your-bot:matrix.org",
    "auth_type": "oidc",
    "oidc_redirect_url": "http://localhost:8765/callback"
  },
  ...
}
</code></pre>
<p><small>📖 <a href="configuration.html#matrix-authentication">Full OIDC guide →</a></small></p>
</details>

<div style="padding: 15px; background: #ffebee; border-left: 4px solid #f44336; margin: 1em 0;">
  <strong>🔒 Security Note:</strong> Never commit your <code>config.json</code> to version control! Add it to <code>.gitignore</code>.
</div>

---

## Step 3️⃣: Run the Bot

Start ChatrixCD:

```bash
# If using binary:
./chatrixcd-linux-x86_64

# If from source:
chatrixcd
```

**What you'll see:**
1. 🖥️ Interactive TUI launches
2. 🔐 Bot logs into Matrix
3. 🔑 Initial sync with encryption keys
4. ✅ Ready! Bot is now online

<div style="padding: 15px; background: #e8f5e9; border-left: 4px solid #4caf50; margin: 1em 0;">
  <strong>✅ Success!</strong> Your bot is now running. Keep this terminal open.
</div>

---

## Step 4️⃣: Invite Bot to Your Room

In your Matrix client (Element, etc.):

<div style="display: flex; flex-direction: column; gap: 15px; margin: 2em 0;">

<div style="display: flex; align-items: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">1️⃣</div>
  <div>
    <strong>Create or open a Matrix room</strong><br>
    <small>Can be encrypted or unencrypted</small>
  </div>
</div>

<div style="display: flex; align-items: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">2️⃣</div>
  <div>
    <strong>Invite your bot</strong><br>
    <small>Use the user_id from your config: <code>@your-bot:matrix.org</code></small>
  </div>
</div>

<div style="display: flex; align-items: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">3️⃣</div>
  <div>
    <strong>Bot auto-accepts the invite</strong><br>
    <small>Look for a friendly greeting! 👋</small>
  </div>
</div>

</div>

---

## Step 5️⃣: Start Using Commands!

Try these commands in your Matrix room:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd help</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📖 See all available commands</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd projects</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📋 List Semaphore projects</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd templates 1</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📄 List templates for project 1</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd run 1 2</code>
  <p style="font-size: 0.9em; margin-top: 10px;">🚀 Run template 2 in project 1</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd status</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📊 Check last task status</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
  <code style="font-weight: bold; color: #3e836b;">!cd logs</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📝 View logs for last task</p>
</div>

</div>

---

## 🎯 Example Workflow

Here's a complete example of running a deployment:

```
You: !cd projects
Bot: 📋 Projects:
     1. Production Website
     2. API Server

You: !cd templates 1
Bot: 📄 Templates for "Production Website":
     1. Deploy to Staging
     2. Deploy to Production

You: !cd run 1 2
Bot: 🚀 Ready to run "Deploy to Production"?
     React with 👍 to confirm or 👎 to cancel

You: [React with 👍]
Bot: ✅ Task started! Task ID: 42
     I'll keep you posted! 📊

[After a few minutes]
Bot: ✅ Task #42 completed successfully! 🎉
     Duration: 3m 24s
```

---

## 🎭 Easter Eggs

ChatrixCD has a fun personality! Try these hidden commands:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 2px dashed #ffc107; border-radius: 8px; background: #fffbeb;">
  <code style="font-weight: bold;">!cd pet</code>
  <p style="font-size: 0.9em; margin-top: 10px;">🐕 Give the bot some love</p>
</div>

<div style="padding: 15px; border: 2px dashed #ffc107; border-radius: 8px; background: #fffbeb;">
  <code style="font-weight: bold;">!cd scold</code>
  <p style="font-size: 0.9em; margin-top: 10px;">😔 Bot feels bad</p>
</div>

</div>

<div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin: 1em 0;">
  <strong>🤫 Shhh!</strong> These are undocumented features. Don't tell everyone! 😉
</div>

---

## 🚀 Next Steps

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">⚙️ Configure More</h3>
  <p>Add custom aliases, configure log tailing, set up OIDC</p>
  <a href="configuration.html">Configuration Guide →</a>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">🖥️ Explore the TUI</h3>
  <p>Learn about the interactive terminal interface features</p>
  <a href="TUI.html">TUI Guide →</a>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">🚀 Deploy to Production</h3>
  <p>systemd, Docker, or native deployment options</p>
  <a href="deployment.html">Deployment Guide →</a>
</div>

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">❓ Need Help?</h3>
  <p>Troubleshooting, FAQ, and getting support</p>
  <a href="support.html">Support Guide →</a>
</div>

</div>

---

<div align="center" style="margin: 3em 0; padding: 2em; background: #e8f5e9; border-radius: 10px;">
  <h2 style="margin-top: 0;">🎉 You're All Set!</h2>
  <p style="font-size: 1.1em;">Your CI/CD automation is now chat-powered. Time to celebrate! 🎊</p>
</div>
