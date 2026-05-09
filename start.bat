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
    copy .env.example .env >nul
    echo Created .env from template. Fill in your BOT_TOKEN and CHAT_ID, then run again.
    start notepad .env
    pause
    exit /b 1
)
if not exist ".env" goto env_missing
findstr /C:"your_token_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] Please fill in your BOT_TOKEN and CHAT_ID in the .env file first.
    start notepad .env
    pause
    exit /b 1
)

:: ── Check Python version ──────────────────────────────────────────────────────
set NEED_PYTHON=0
set MIN_MINOR=11
set INSTALL_VER=3.13.3

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Python not found.
    set NEED_PYTHON=1
) else (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
    for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
        set PY_MAJOR=%%a
        set PY_MINOR=%%b
    )
    if %PY_MAJOR% LSS 3 (
        echo [*] Python %PYVER% is too old.
        set NEED_PYTHON=1
    ) else if %PY_MAJOR% EQU 3 (
        if %PY_MINOR% LSS %MIN_MINOR% (
            echo [*] Python %PYVER% is too old ^(need 3.%MIN_MINOR%+^).
            set NEED_PYTHON=1
        ) else (
            echo [+] Python %PYVER% OK
        )
    )
)

if %NEED_PYTHON% equ 1 (
    echo [*] Downloading Python %INSTALL_VER%...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%INSTALL_VER%/python-%INSTALL_VER%-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    if %errorlevel% neq 0 (
        echo [!] Download failed. Please install Python from https://www.python.org
        pause
        exit /b 1
    )
    echo [*] Installing Python %INSTALL_VER%...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0
    del "%TEMP%\python_installer.exe"
    echo [+] Python installed! Please close this window and run start.bat again.
    pause
    exit /b 0
)

:: ── Check uv ──────────────────────────────────────────────────────────────────
python -m uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing uv...
    python -m pip install uv --quiet
)

:: ── Setup virtual environment ─────────────────────────────────────────────────
if not exist ".venv" (
    echo [*] Setting up environment and installing dependencies...
    python -m uv venv .venv
    python -m uv pip install -r requirements.txt --python .venv\Scripts\python.exe
    echo [+] Setup complete!
)

:: ── Run ───────────────────────────────────────────────────────────────────────
echo [+] Starting FlowBot...
echo.
".venv\Scripts\python.exe" main.py
pause
