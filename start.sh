#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  FlowBot — Focus Telegram Bot"
echo "=========================================="
echo ""

# ── Check .env ─────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[!] Created .env from template."
    echo "    Fill in BOT_TOKEN and CHAT_ID, save the file, then run start.command again."
    open -e .env 2>/dev/null || nano .env
    exit 1
fi
if grep -q "your_token_here\|your_chat_id_here" .env; then
    echo "[!] Please fill in your BOT_TOKEN and CHAT_ID in the .env file first."
    open -e .env 2>/dev/null || nano .env
    exit 1
fi

# ── Check Python version ───────────────────────────────────────────────────────
MIN_MAJOR=3
MIN_MINOR=11
INSTALL_VER="3.13.3"
NEED_PYTHON=0

if command -v python3 &>/dev/null; then
    PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')

    if [ "$PY_MAJOR" -lt "$MIN_MAJOR" ] || { [ "$PY_MAJOR" -eq "$MIN_MAJOR" ] && [ "$PY_MINOR" -lt "$MIN_MINOR" ]; }; then
        echo "[*] Python $PY_VER is too old (need ${MIN_MAJOR}.${MIN_MINOR}+). Updating..."
        NEED_PYTHON=1
    else
        echo "[+] Python $PY_VER OK"
    fi
else
    echo "[*] Python not found."
    NEED_PYTHON=1
fi

if [ "$NEED_PYTHON" -eq 1 ]; then
    echo "[*] Downloading Python $INSTALL_VER..."
    PKG="/tmp/python_installer.pkg"
    curl -L "https://www.python.org/ftp/python/${INSTALL_VER}/python-${INSTALL_VER}-macos11.pkg" -o "$PKG"
    if [ $? -ne 0 ]; then
        echo "[!] Download failed. Please install Python from https://www.python.org"
        exit 1
    fi
    echo ""
    echo "[*] Opening Python installer..."
    echo "    Complete the installation, then run start.command again."
    open "$PKG"
    exit 0
fi

# ── Check uv ───────────────────────────────────────────────────────────────────
if ! python3 -m uv --version &>/dev/null 2>&1; then
    echo "[*] Installing uv..."
    python3 -m pip install uv --quiet
fi

# ── Setup virtual environment ──────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "[*] Setting up environment and installing dependencies..."
    python3 -m uv venv .venv
    python3 -m uv pip install -r requirements.txt --python .venv/bin/python
    echo "[+] Setup complete!"
fi

# ── Setup LaunchAgent (autostart + background) ────────────────────────────────
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.flowbot.plist"
PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python"

mkdir -p "$PLIST_DIR"
cat > "$PLIST_FILE" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.flowbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/flowbot.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/flowbot_error.log</string>
</dict>
</plist>
PLIST

# Stop previous instance if running
launchctl unload "$PLIST_FILE" 2>/dev/null
sleep 1

# Start in background
launchctl load "$PLIST_FILE"

echo ""
echo "[+] FlowBot запущен в фоне!"
echo "    Автозапуск при входе в систему — настроен."
echo ""
echo "[i] Если macOS запросит доступ к Accessibility:"
echo "    Системные настройки → Конфиденциальность → Универсальный доступ → разрешить Терминал"
echo ""
echo "    Чтобы остановить бота:"
echo "    launchctl unload ~/Library/LaunchAgents/com.flowbot.plist"
echo ""
