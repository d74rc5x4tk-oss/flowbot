#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  FlowBot — Focus Telegram Bot"
echo "=========================================="
echo ""

# ── Helper: find working python3 >= 3.11 ──────────────────────────────────────
find_python() {
    for py in python3 /usr/local/bin/python3 /usr/bin/python3 \
              /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
              /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
              /Library/Frameworks/Python.framework/Versions/3.11/bin/python3; do
        if command -v "$py" &>/dev/null 2>&1; then
            local minor
            minor=$("$py" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
            if [ -n "$minor" ] && [ "$minor" -ge 11 ]; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

# ── Step 1: .env ───────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

if grep -q "your_token_here\|your_chat_id_here" .env; then
    echo "[!] Нужно заполнить токены в файле .env"
    echo "    Открываю файл..."
    open -e .env
    echo ""
    echo "    Заполни BOT_TOKEN и CHAT_ID, сохрани файл (Cmd+S),"
    echo -n "    затем нажми Enter здесь чтобы продолжить... "
    read -r

    if grep -q "your_token_here\|your_chat_id_here" .env; then
        echo "[!] Токены не заполнены. Запусти файл ещё раз."
        exit 1
    fi
fi
echo "[+] Токены OK"

# ── Step 2: Python ─────────────────────────────────────────────────────────────
PYTHON3=$(find_python)

if [ -z "$PYTHON3" ]; then
    INSTALL_VER="3.13.3"
    echo "[*] Python не найден. Скачиваю Python $INSTALL_VER..."
    PKG="/tmp/python_installer.pkg"
    curl -L --progress-bar "https://www.python.org/ftp/python/${INSTALL_VER}/python-${INSTALL_VER}-macos11.pkg" -o "$PKG"
    if [ $? -ne 0 ]; then
        echo "[!] Ошибка скачивания. Установи Python вручную: https://www.python.org"
        exit 1
    fi
    echo ""
    echo "[*] Открываю установщик Python..."
    open "$PKG"
    echo ""
    echo "    Установи Python через открывшийся установщик (нажимай Продолжить → Установить)."
    echo -n "    Когда установка завершится — нажми Enter здесь... "
    read -r
    echo ""

    PYTHON3=$(find_python)
    if [ -z "$PYTHON3" ]; then
        echo "[!] Python всё ещё не найден. Попробуй запустить файл заново."
        exit 1
    fi
fi

PY_VER=$("$PYTHON3" --version 2>&1 | awk '{print $2}')
echo "[+] Python $PY_VER OK"

# ── Step 3: uv ─────────────────────────────────────────────────────────────────
if ! "$PYTHON3" -m uv --version &>/dev/null 2>&1; then
    echo "[*] Устанавливаю uv..."
    "$PYTHON3" -m pip install uv --quiet
fi

# ── Step 4: Virtual environment ────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "[*] Устанавливаю зависимости..."
    "$PYTHON3" -m uv venv .venv
    "$PYTHON3" -m uv pip install -r requirements.txt --python .venv/bin/python
    echo "[+] Готово!"
fi

# ── Step 5: LaunchAgent (autostart + background) ──────────────────────────────
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

launchctl unload "$PLIST_FILE" 2>/dev/null
sleep 1
launchctl load "$PLIST_FILE"

echo ""
echo "=========================================="
echo "  FlowBot запущен!"
echo ""
echo "  Работает в фоне — окно можно закрыть"
echo "  Запускается автоматически при входе"
echo "  Иконка появится в меню-баре вверху"
echo ""
echo "  Если macOS запросит доступ:"
echo "  Системные настройки → Конфиденциальность"
echo "  → Универсальный доступ → разрешить Терминал"
echo "=========================================="
echo ""
