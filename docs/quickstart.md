---
layout: default
title: Quick Start
nav_order: 4
---

# ⚡ Quick Start Guide

Get ChatrixCD up and running in **2 minutes**! 🚀

<div style="padding: 15px; border-left: 4px solid #ffc107; margin: 1em 0;">
  <strong>⏱️ Time to Success:</strong> ~2 minutes<br>
  <strong>📋 What You'll Need:</strong> Matrix account, Semaphore UI access<br>
  <strong>🎯 What You'll Get:</strong> Fully working CI/CD bot in your chat!
</div>

---

## Step 1️⃣: Download & Run

<div style="padding: 20px; border: 2px solid #3e836b; border-radius: 10px;">
  <h3 style="margin-top: 0;">📦 Download from the Download Page</h3>
  <p><strong>✅ No Python required!</strong> Pre-built binaries for Linux.</p>
  <p>Visit the <a href="download.html">Download Page</a> to get the latest binary for your platform.</p>
  <pre><code># Example for x86_64:
wget https://github.com/CJFWeatherhead/ChatrixCD/releases/latest/download/chatrixcd-linux-x86_64.dist.tar.gz
tar -xzf chatrixcd-linux-x86_64.dist.tar.gz
cd chatrixcd-linux-x86_64.dist
./chatrixcd</code></pre>
</div>

<div style="padding: 15px; border-left: 4px solid #4caf50; margin: 1em 0;">
  <strong>✅ Success!</strong> The bot will guide you through configuration if <code>config.json</code> doesn't exist. Keep this terminal open.
</div>

---

## Step 2️⃣: Invite Bot to Your Room

In your Matrix client (Element, etc.):

<div style="display: flex; flex-direction: column; gap: 15px; margin: 2em 0;">

<div style="display: flex; align-items: center; padding: 15px; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">1️⃣</div>
  <div>
    <strong>Create or open a Matrix room</strong><br>
    <small>Can be encrypted or unencrypted</small>
  </div>
</div>

<div style="display: flex; align-items: center; padding: 15px; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">2️⃣</div>
  <div>
    <strong>Invite your bot</strong><br>
    <small>Use the user_id from your config: <code>@your-bot:matrix.org</code></small>
  </div>
</div>

<div style="display: flex; align-items: center; padding: 15px; border-radius: 8px;">
  <div style="font-size: 2em; margin-right: 15px; min-width: 40px;">3️⃣</div>
  <div>
    <strong>Bot auto-accepts the invite</strong><br>
    <small>Look for a friendly greeting! 👋</small>
  </div>
</div>

</div>

---

## Step 3️⃣: Start Using Commands!

Try these commands in your Matrix room:

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 2em 0;">

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd help</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📖 See all available commands</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd projects</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📋 List Semaphore projects</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd templates 1</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📄 List templates for project 1</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd run 1 2</code>
  <p style="font-size: 0.9em; margin-top: 10px;">🚀 Run template 2 in project 1</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd status</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📊 Check last task status</p>
</div>

<div style="padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
  <code style="font-weight: bold; color: #3e836b;">!cd logs</code>
  <p style="font-size: 0.9em; margin-top: 10px;">📝 View logs for last task</p>
</div>

</div>

---

## 🔖 Command Aliases

Speed up common actions by creating your own shortcuts:

- Add: `!cd aliases add <alias> <command>`
  - Works with prefixed or unprefixed commands
  - Example: `!cd aliases add deploy run 4 5 --tags=prod --arg="--dry-run"`
- Remove: `!cd aliases remove <alias>`
- List: `!cd aliases`

Aliases expand with any extra arguments you append when using them. For example, if `deploy` maps to `run 4 5`, then typing `!cd deploy --tags=prod` runs `!cd run 4 5 --tags=prod`.

> Note: The base command must be a valid bot command; extra flags are passed through unchanged.

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

<div style="padding: 15px; border: 2px dashed #ffc107; border-radius: 8px;">
  <code style="font-weight: bold;">!cd pet</code>
  <p style="font-size: 0.9em; margin-top: 10px;">🐕 Give the bot some love</p>
</div>

<div style="padding: 15px; border: 2px dashed #ffc107; border-radius: 8px;">
  <code style="font-weight: bold;">!cd scold</code>
  <p style="font-size: 0.9em; margin-top: 10px;">😔 Bot feels bad</p>
</div>

</div>

<div style="padding: 15px; border-left: 4px solid #ffc107; margin: 1em 0;">
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

<div align="center" style="margin: 3em 0; padding: 2em; border-radius: 10px;">
  <h2 style="margin-top: 0;">🎉 You're All Set!</h2>
  <p style="font-size: 1.1em;">Your CI/CD automation is now chat-powered. Time to celebrate! 🎊</p>
</div>
