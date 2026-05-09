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

### 1. Download FlowBot

Go to 👉 https://github.com/d74rc5x4tk-oss/flowbot, click **Code → Download ZIP**, extract the folder anywhere.

### 2. Run

Open **Terminal** (`Cmd + Space` → type `Terminal` → Enter), then drag the extracted folder into the Terminal window and press Enter to navigate into it. Then run:

```bash
bash start.sh
```

**That's it.** The script will:
- Download and install Python automatically if needed
- Install all dependencies
- Open `.env` for you to fill in your tokens (BOT_TOKEN and CHAT_ID)
- Start the bot

> **macOS note:** On first run, macOS may ask for Accessibility permission.
> Go to **System Settings → Privacy & Security → Accessibility** and allow Terminal.

---

## Installation on Windows (no experience required)

### 1. Download FlowBot

Go to 👉 https://github.com/d74rc5x4tk-oss/flowbot, click **Code → Download ZIP**, extract the folder anywhere.

### 2. Run

Double-click **`start.bat`**

**That's it.** The script will:
- Download and install Python automatically if needed
- Install all dependencies
- Open `.env` for you to fill in your tokens (BOT_TOKEN and CHAT_ID)
- Start the bot

---

## Distracting sites

Tracked by default: YouTube, Instagram, TikTok, Twitch, Netflix, Twitter/X, Facebook, VK, Kinopoisk.

To edit the list, open `monitor.py` and find `DISTRACTING_APPS`.

---

## Autostart on Windows

To make FlowBot start automatically with Windows:
1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `start.bat` in that folder
