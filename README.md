# FlowBot — Telegram Focus Bot

A Telegram bot that monitors your PC/Mac activity and helps you stay focused. Built for people with ADHD and anyone who wants to build better work habits.

## Features

- Sends a Telegram notification if no mouse/keyboard activity for 5 minutes
- Detects distracting websites (YouTube, Instagram, TikTok, etc.) and warns you every 5 seconds
- Work day management via inline buttons: short breaks (4×15 min) and lunch (1×60 min)
- Planning phase at the start of each day (10 min to set up tasks)
- Streak system: calendar streaks, Mon–Fri workday streaks, distraction-free streaks
- Achievements and end-of-day productivity report
- Todoist integration in daily report (optional)
- State is saved on restart

## Platform Support

| Feature | Windows | macOS |
|---|---|---|
| Idle notifications | ✅ | ✅ |
| Distraction detection (Chrome/Safari/Firefox) | ✅ | ✅ |
| Telegram bot | ✅ | ✅ |

---

## Setup

### Step 1 — Create a Telegram bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### Step 2 — Get your Chat ID

Send any message to your new bot, then open this URL in a browser:
```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```
Find the `"id"` field inside `"chat"` — that's your Chat ID.

---

## Installation on macOS (no experience required)

### 1. Install Python

Download and install Python 3 from the official site:
👉 https://www.python.org/downloads/

Open the installer and follow the steps. When done, open **Terminal** (press `Cmd + Space`, type `Terminal`, press Enter).

### 2. Download FlowBot

In Terminal, run these commands one by one:

```bash
curl -L https://github.com/d74rc5x4tk-oss/flowbot/archive/refs/heads/main.zip -o flowbot.zip
unzip flowbot.zip
cd flowbot-main
```

### 3. Install dependencies

```bash
pip3 install uv
uv venv .venv
uv pip install -r requirements.txt --python .venv/bin/python
```

### 4. Configure your tokens

```bash
cp .env.example .env
open -e .env
```

A text editor will open. Fill in your values:
```
BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
TODOIST_TOKEN=your_todoist_token_here  # optional
```
Save and close the file.

### 5. Run

```bash
bash start.sh
```

> **macOS note:** On first run, macOS will ask for permission to monitor keyboard/mouse input.
> Go to **System Settings → Privacy & Security → Accessibility** and allow Terminal.

---

## Installation on Windows

1. Install Python 3 from https://www.python.org/downloads/ (check "Add to PATH" during install)
2. Download the ZIP from GitHub and extract it
3. Copy `.env.example` to `.env` and fill in your tokens
4. Double-click `start.bat`

---

## Distracting sites

Tracked by default: YouTube, Instagram, TikTok, Twitch, Netflix, Twitter/X, Facebook, VK, Kinopoisk.

To edit the list, open `monitor.py` and find `DISTRACTING_APPS`.

---

## Autostart on Windows

To make FlowBot start automatically with Windows:
1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `start.bat` in that folder
