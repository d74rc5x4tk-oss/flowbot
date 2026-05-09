# Activity Monitor — Focus Bot

Telegram-бот который следит за активностью на компьютере и помогает держать фокус.

## Что делает

- Уведомляет в Telegram если 5 минут не было активности мыши/клавиатуры
- Обнаруживает отвлекающие сайты (YouTube, Instagram, TikTok и др.) и присылает предупреждение каждые 5 секунд
- Управление рабочим днём через кнопки: перерывы (4×15 мин) и обед (1×60 мин)
- Состояние сохраняется при перезапуске

## Поддерживаемые платформы

| Функция | Windows | macOS |
|---|---|---|
| Уведомления о бездействии | ✅ | ✅ |
| Обнаружение вкладок (Chrome/Safari/Firefox) | ✅ | ✅ |
| Telegram бот | ✅ | ✅ |

## Установка

### 1. Создать Telegram бота

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Напиши `/newbot` и следуй инструкциям
3. Скопируй полученный токен

### 2. Получить свой Chat ID

Напиши любое сообщение своему боту, затем открой:
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
Найди поле `"id"` внутри `"chat"`.

### 3. Установить зависимости

```bash
# Установить uv (если нет)
pip install uv

# Создать окружение и установить пакеты
uv venv .venv
uv pip install -r requirements.txt --python .venv/Scripts/python.exe  # Windows
uv pip install -r requirements.txt --python .venv/bin/python           # macOS
```

### 4. Настроить .env

Скопируй `.env.example` в `.env` и заполни:
```
BOT_TOKEN=твой_токен_здесь
CHAT_ID=твой_chat_id_здесь
```

### 5. Запустить

**Windows:** двойной клик на `start.bat`

**macOS:**
```bash
.venv/bin/python main.py
```

> На macOS потребуется разрешить доступ к специальным возможностям (Accessibility) в System Settings → Privacy & Security → Accessibility

## Отвлекающие сайты

По умолчанию отслеживаются: YouTube, ВКонтакте, Instagram, TikTok, Twitch, Netflix, КиноПоиск, Twitter/X, Facebook.

Список можно изменить в `monitor.py` → `DISTRACTING_APPS`.
