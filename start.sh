#!/bin/bash
cd "$(dirname "$0")"

# Создаём окружение если его нет
if [ ! -d ".venv" ]; then
    echo "Создаю виртуальное окружение..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "Запускаю Activity Monitor..."
.venv/bin/python main.py
