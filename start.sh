#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================="
echo "  FlowBot — Focus Telegram Bot"
echo "=========================================="
echo ""

# ── Check .env ─────────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "[!] .env file not found!"
    echo "    Copy .env.example to .env and fill in your tokens."
    cp .env.example .env
    echo ""
    echo "Created .env from template. Opening it for you..."
    echo "Fill in BOT_TOKEN and CHAT_ID, save the file, then run start.sh again."
    open -e .env 2>/dev/null || nano .env
    exit 1
fi

# ── Check for empty tokens ─────────────────────────────────────────────────────
if grep -q "your_token_here\|your_chat_id_here" .env; then
    echo "[!] Please fill in your BOT_TOKEN and CHAT_ID in the .env file first."
    echo "    Opening .env..."
    open -e .env 2>/dev/null || nano .env
    exit 1
fi

# ── Check Python ───────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "[*] Python not found. Downloading Python 3.13.3..."
    PYTHON_PKG="/tmp/python_installer.pkg"
    curl -L "https://www.python.org/ftp/python/3.13.3/python-3.13.3-macos11.pkg" -o "$PYTHON_PKG"
    if [ $? -ne 0 ]; then
        echo "[!] Download failed. Please install Python from https://www.python.org"
        exit 1
    fi
    echo ""
    echo "[*] Opening Python installer..."
    echo "    Please complete the installation, then run start.sh again."
    open "$PYTHON_PKG"
    exit 0
fi

# ── Check uv ───────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null && ! python3 -m uv --version &>/dev/null 2>&1; then
    echo "[*] Installing uv package manager..."
    python3 -m pip install uv --quiet
fi

# ── Setup virtual environment ──────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "[*] Setting up virtual environment..."
    python3 -m uv venv .venv
    echo "[*] Installing dependencies..."
    python3 -m uv pip install -r requirements.txt --python .venv/bin/python
    echo "[+] Setup complete!"
fi

# ── macOS accessibility permission hint ────────────────────────────────────────
echo ""
echo "[i] Note: On first run, macOS may ask for Accessibility permission."
echo "    If prompted: System Settings → Privacy & Security → Accessibility → allow Terminal"
echo ""

# ── Run ────────────────────────────────────────────────────────────────────────
echo "[+] Starting FlowBot..."
echo ""
.venv/bin/python main.py
