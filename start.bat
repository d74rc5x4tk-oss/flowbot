@echo off
title FlowBot Setup
cd /d "%~dp0"
chcp 65001 >nul 2>&1

echo ==========================================
echo   FlowBot — Focus Telegram Bot
echo ==========================================
echo.

:: ── Check .env ────────────────────────────────────────────────────────────────
if not exist ".env" (
    echo [!] .env file not found!
    echo     Copy .env.example to .env and fill in your tokens:
    echo     - BOT_TOKEN  : your Telegram bot token
    echo     - CHAT_ID    : your Telegram chat ID
    echo.
    copy .env.example .env >nul
    echo Created .env from template. Open it and fill in your tokens, then run again.
    start notepad .env
    pause
    exit /b 1
)

:: ── Check Python ──────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Python not found. Downloading Python 3.13.3...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe' -OutFile '%TEMP%\python_installer.exe'" 2>&1
    if %errorlevel% neq 0 (
        echo [!] Download failed. Please install Python manually from https://www.python.org
        pause
        exit /b 1
    )
    echo [*] Installing Python silently...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1
    del "%TEMP%\python_installer.exe"
    echo [+] Python installed!
    echo     Please close this window and run start.bat again.
    pause
    exit /b 0
)

:: ── Check uv ──────────────────────────────────────────────────────────────────
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing uv package manager...
    python -m pip install uv --quiet
)

:: ── Setup virtual environment ─────────────────────────────────────────────────
if not exist ".venv" (
    echo [*] Setting up virtual environment...
    python -m uv venv .venv
    echo [*] Installing dependencies...
    python -m uv pip install -r requirements.txt --python .venv\Scripts\python.exe
    echo [+] Setup complete!
)

:: ── Run ───────────────────────────────────────────────────────────────────────
echo [+] Starting FlowBot...
echo.
".venv\Scripts\python.exe" main.py
pause
