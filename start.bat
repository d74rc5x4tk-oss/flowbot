@echo off
title Focus Monitor
echo Запускаю Activity Monitor...
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py
pause
