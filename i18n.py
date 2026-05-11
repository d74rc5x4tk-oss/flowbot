"""Translations for FlowBot. Supported: ru, en."""

_T = {
    # ── keyboard buttons ───────────────────────────────────────────────────────
    "btn_start":        {"ru": "▶️ Начать рабочий день",          "en": "▶️ Start work day"},
    "btn_ready":        {"ru": "✅ Готов, начинаем работать!",     "en": "✅ Ready, let's work!"},
    "btn_skip_plan":    {"ru": "⏭ Пропустить планирование",       "en": "⏭ Skip planning"},
    "btn_return_break": {"ru": "🏃 Вернуться к работе досрочно",   "en": "🏃 Return early"},
    "btn_break_short":  {"ru": "⏸ Перерыв 15 мин ({left} ост.)", "en": "⏸ Break 15 min ({left} left)"},
    "btn_lunch":        {"ru": "🍽 Обед 60 мин",                   "en": "🍽 Lunch 60 min"},
    "btn_end_day":      {"ru": "⏹ Закончить день",                "en": "⏹ End day"},

    # ── startup messages ───────────────────────────────────────────────────────
    "welcome":           {"ru": "👋 Привет! Я твой фокус-бот.",   "en": "👋 Hi! I'm your focus bot."},
    "start_day_prompt":  {"ru": "🤖 Бот запущен. Нажми ▶️ чтобы начать день!", "en": "🤖 Bot started. Press ▶️ to begin your day!"},
    "restart_working":   {"ru": "🔄 Бот перезапущен. Рабочий день уже идёт 💪\nПерерывов: {sb}/{max_sb}  |  Обед: {lunch}\n{streak_bar} {streak} дн.", "en": "🔄 Bot restarted. Work day in progress 💪\nBreaks: {sb}/{max_sb}  |  Lunch: {lunch}\n{streak_bar} {streak} d."},
    "restart_planning":  {"ru": "🔄 Бот перезапущен. Осталось {mins} мин на планирование 📋", "en": "🔄 Bot restarted. {mins} min left for planning 📋"},
    "restart_break":     {"ru": "🔄 Бот перезапущен. Ты на перерыве — осталось {mins}м {secs}с", "en": "🔄 Bot restarted. On break — {mins}m {secs}s left"},
    "lunch_used":        {"ru": "❌ использован",                  "en": "❌ used"},
    "lunch_avail":       {"ru": "✅ доступен",                     "en": "✅ available"},

    # ── planning ───────────────────────────────────────────────────────────────
    "planning_start":    {"ru": "📋 *Время планирования!*\nУ тебя {mins} минут чтобы составить план на день в Todoist.\nКогда готов — нажми кнопку ниже.", "en": "📋 *Planning time!*\nYou have {mins} minutes to plan your day in Todoist.\nWhen ready — press the button below."},
    "planning_tasks":    {"ru": "📌 *Задачи на сегодня:*",         "en": "📌 *Today's tasks:*"},
    "planning_ended":    {"ru": "⏱ Время планирования вышло. *Рабочий день начат!* 🚀", "en": "⏱ Planning time is up. *Work day started!* 🚀"},
    "day_started":       {"ru": "🚀 Рабочий день начат! Удачи 💪", "en": "🚀 Work day started! Good luck 💪"},

    # ── breaks ─────────────────────────────────────────────────────────────────
    "break_short_start": {"ru": "⏸ Перерыв 15 минут. Отдыхай!",  "en": "⏸ 15-minute break. Rest up!"},
    "break_long_start":  {"ru": "🍽 Обед 60 минут. Приятного аппетита!", "en": "🍽 60-minute lunch. Enjoy your meal!"},
    "break_ended":       {"ru": "⏰ Перерыв закончился, возвращайся к работе! 💼", "en": "⏰ Break is over, get back to work! 💼"},
    "return_early":      {"ru": "🏃 Вернулся досрочно! Продолжаем 💪", "en": "🏃 Returned early! Let's keep going 💪"},

    # ── notifications ──────────────────────────────────────────────────────────
    "idle_first":        {"ru": "😴 Ты куда пропал? Вернись к работе!", "en": "😴 Where did you go? Get back to work!"},
    "idle_repeat":       {"ru": "👀 Всё ещё здесь?",               "en": "👀 Still there?"},
    "distraction":       {"ru": "🚨 Это {app}, не работа! Закрывай и фокусируйся.", "en": "🚨 That's {app}, not work! Close it and focus."},

    # ── end of day report ──────────────────────────────────────────────────────
    "report_header":     {"ru": "⏹ *День завершён!*",             "en": "⏹ *Day complete!*"},
    "report_work":       {"ru": "⏱ Работал: {t}",                 "en": "⏱ Worked: {t}"},
    "report_break":      {"ru": "☕ Отдыхал: {t}",                 "en": "☕ Rested: {t}"},
    "report_dist":       {"ru": "🚨 Отвлечений: {n}",              "en": "🚨 Distractions: {n}"},
    "report_todoist_no": {"ru": "📋 Todoist: не подключён",        "en": "📋 Todoist: not connected"},
    "report_todoist_empty": {"ru": "📋 Todoist: задач на сегодня нет", "en": "📋 Todoist: no tasks today"},
    "report_todoist":    {"ru": "📋 Todoist: {done}/{total} задач ({pct}%)", "en": "📋 Todoist: {done}/{total} tasks ({pct}%)"},
    "report_streaks":    {"ru": "🔥 Стрик: {d} дн.  ⚡ Чистый: {c} дн.  💼 Рабочих: {w} дн.", "en": "🔥 Streak: {d} d.  ⚡ Clean: {c} d.  💼 Workdays: {w} d."},
    "report_score":      {"ru": "💡 Оценка: *{score}/10* — {grade}", "en": "💡 Score: *{score}/10* — {grade}"},
    "grade_galley":      {"ru": "⛓ Раб на галерах",               "en": "⛓ Absolute beast"},
    "grade_worker":      {"ru": "💪 Трудяга-работяга",             "en": "💪 Hard worker"},
    "grade_growing":     {"ru": "📈 Есть куда расти",              "en": "📈 Room to grow"},
    "grade_lazy":        {"ru": "🛋 Считай не работал",            "en": "🛋 Barely worked"},

    # ── weekly report ──────────────────────────────────────────────────────────
    "week_header":       {"ru": "📊 *Итоги недели*",               "en": "📊 *Weekly summary*"},
    "week_total":        {"ru": "⏱ Всего: {t}",                    "en": "⏱ Total: {t}"},
    "week_dist":         {"ru": "🚨 Отвлечений: {n}",              "en": "🚨 Distractions: {n}"},
    "week_streaks":      {"ru": "🔥 Стрик: {d} дн. | 💼 Рабочих: {w} дн.", "en": "🔥 Streak: {d} d. | 💼 Workdays: {w} d."},
    "week_best":         {"ru": "🏆 Лучший день: {day}",           "en": "🏆 Best day: {day}"},
    "weekdays":          {"ru": ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"], "en": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]},

    # ── achievements ──────────────────────────────────────────────────────────
    "ach_header":        {"ru": "🏅 *Твои ачивки*",                "en": "🏅 *Your achievements*"},
    "ach_none":          {"ru": "Пока нет ачивок. Начни работать! 💪", "en": "No achievements yet. Start working! 💪"},
    "ach_new":           {"ru": "🏅 Новая ачивка!\n{emoji} *{title}*\n_{desc}_", "en": "🏅 New achievement!\n{emoji} *{title}*\n_{desc}_"},

    # ── time formatting ────────────────────────────────────────────────────────
    "time_hm":           {"ru": "{h}ч {m}мин",                     "en": "{h}h {m}min"},
    "time_m":            {"ru": "{m}мин",                          "en": "{m}min"},

    # ── tray / menu bar ────────────────────────────────────────────────────────
    "tray_running":      {"ru": "FlowBot — работает",              "en": "FlowBot — running"},
    "tray_restart":      {"ru": "Перезапустить бота",              "en": "Restart bot"},
    "tray_stop":         {"ru": "Остановить бота",                 "en": "Stop bot"},

    # ── misc ───────────────────────────────────────────────────────────────────
    "days_abbr":         {"ru": "дн.",                             "en": "d."},
    "report_overdue":    {"ru": "📋 Незакрытые задачи:",           "en": "📋 Uncompleted tasks:"},
}


def t(key: str, lang: str, **kwargs) -> str:
    """Return translated string for key in given language."""
    row = _T.get(key, {})
    text = row.get(lang) or row.get("en") or key
    return text.format(**kwargs) if kwargs else text


def detect_lang(language_code: str | None) -> str:
    """Map Telegram language_code to supported lang ('ru' or 'en')."""
    if language_code and language_code.lower().startswith("ru"):
        return "ru"
    return "en"


def os_lang() -> str:
    """Detect OS language for tray/menubar labels."""
    import locale
    try:
        loc = locale.getdefaultlocale()[0] or ""
        return "ru" if loc.lower().startswith("ru") else "en"
    except Exception:
        return "en"
