import asyncio
import os
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from state import AppState, MAX_SHORT_BREAKS
from achievements import check_new_achievements, format_achievement

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# ── keyboards ─────────────────────────────────────────────────────────────────

def _keyboard_for_state(state: AppState) -> InlineKeyboardMarkup:
    if state.is_off:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Начать рабочий день", callback_data="start")],
        ])
    if state.is_planning:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Готов, начинаем работать!", callback_data="ready")],
            [InlineKeyboardButton("⏭ Пропустить планирование", callback_data="skip_plan")],
        ])
    if state.is_on_break:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏃 Вернуться к работе досрочно", callback_data="return_break")],
        ])
    # working
    break_row = []
    if state.can_short_break:
        left = MAX_SHORT_BREAKS - state.short_breaks_today
        break_row.append(InlineKeyboardButton(
            f"⏸ Перерыв 15 мин ({left} ост.)", callback_data="break_short"
        ))
    if state.can_long_break:
        break_row.append(InlineKeyboardButton("🍽 Обед 60 мин", callback_data="break_long"))
    rows = []
    if break_row:
        rows.append(break_row)
    rows.append([InlineKeyboardButton("⏹ Закончить день", callback_data="end")])
    return InlineKeyboardMarkup(rows)


# ── formatting helpers ────────────────────────────────────────────────────────

def _fmt_time(seconds: int) -> str:
    h, m = divmod(seconds // 60, 60)
    if h:
        return f"{h}ч {m}мин"
    return f"{m}мин"


def _streak_bar(n: int) -> str:
    return "🔥" * min(n, 7) + (f" ×{n}" if n > 7 else "")


async def _fetch_todoist_tasks(token: str) -> list[str]:
    """Возвращает список названий активных задач на сегодня."""
    if not HAS_HTTPX or not token:
        return []
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.todoist.com/api/v1/tasks",
                headers=headers,
                params={"filter": "today | overdue"},
            )
            if r.status_code != 200:
                return []
            results = r.json().get("results", [])
            return [t["content"] for t in results]
    except Exception:
        return []


async def _fetch_todoist_stats(token: str) -> dict | None:
    """Возвращает {completed, total} задач Todoist за сегодня."""
    if not HAS_HTTPX or not token:
        return None
    today = date.today().isoformat()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            # Активные (невыполненные) задачи на сегодня
            r = await client.get(
                "https://api.todoist.com/api/v1/tasks",
                headers=headers,
                params={"filter": "today | overdue"},
            )
            active = len(r.json().get("results", [])) if r.status_code == 200 else 0

            # Выполненные сегодня — получаем проекты и запрашиваем архив каждого
            rp = await client.get("https://api.todoist.com/api/v1/projects", headers=headers)
            completed = 0
            if rp.status_code == 200:
                projects = rp.json().get("results", [])
                for proj in projects:
                    ra = await client.get(
                        "https://api.todoist.com/api/v1/archive/items",
                        headers=headers,
                        params={
                            "project_id": proj["id"],
                            "since": f"{today}T00:00:00",
                            "until": f"{today}T23:59:59",
                        },
                    )
                    if ra.status_code == 200:
                        completed += len(ra.json().get("items", []))

        return {"completed": completed, "total": completed + active}
    except Exception:
        return None


def _build_end_of_day_report(stats: dict, todoist: dict | None,
                              state: AppState) -> str:
    work_str  = _fmt_time(stats["work_seconds"])
    break_str = _fmt_time(stats["break_seconds"])
    dist      = stats["distractions"]

    # Оценка продуктивности
    # Фокус (40%): 0% если >10 отвлечений, 100% если 0
    focus_pct = max(0, 1 - dist / 10)
    score = focus_pct * 40

    # Время работы (20%): 8 часов = 100%
    work_pct = min(1, stats["work_seconds"] / (8 * 3600))
    score += work_pct * 20

    # Todoist (40%)
    todoist_line = ""
    if todoist is None:
        score += 20  # нейтральный бонус если нет токена
        todoist_line = "📋 Todoist: не подключён\n"
    elif todoist["total"] == 0:
        score += 20
        todoist_line = "📋 Todoist: задач на сегодня нет\n"
    else:
        t_pct = todoist["completed"] / todoist["total"]
        score += t_pct * 40
        todoist_line = (
            f"📋 Todoist: {todoist['completed']}/{todoist['total']} задач "
            f"({int(t_pct * 100)}%)\n"
        )

    score = min(10, round(score / 10, 1))

    work_hours = stats["work_seconds"] / 3600
    if work_hours >= 9:
        grade = "⛓ Раб на галерах"
    elif work_hours >= 6:
        grade = "💪 Трудяга-работяга"
    elif work_hours >= 3:
        grade = "📈 Есть куда расти"
    else:
        grade = "🛋 Считай не работал"

    streak_line = (
        f"🔥 Стрик: {state.streak_days} дн.  "
        f"⚡ Чистый: {state.streak_clean} дн.  "
        f"💼 Рабочих: {state.streak_workdays} дн."
    )

    return (
        f"⏹ *День завершён!*\n\n"
        f"⏱ Работал: {work_str}\n"
        f"☕ Отдыхал: {break_str}\n"
        f"🚨 Отвлечений: {dist}\n"
        f"{todoist_line}\n"
        f"{streak_line}\n\n"
        f"💡 Оценка: *{score}/10* — {grade}"
    )


def _build_weekly_report(state: AppState) -> str:
    today = date.today()
    lines = ["📊 *Итоги недели*\n"]
    total_work = 0
    total_dist = 0
    total_done = 0
    best_day = None
    best_work = 0

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        ds = d.isoformat()
        wd = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][d.weekday()]
        if ds in state.daily_stats:
            st = state.daily_stats[ds]
            w = st["work_seconds"]
            total_work += w
            total_dist += st["distractions"]
            hours = w / 3600
            bar = "█" * int(hours) + "░" * max(0, 8 - int(hours))
            lines.append(f"{wd} {bar} {_fmt_time(w)}")
            if w > best_work:
                best_work = w
                best_day = wd
        else:
            lines.append(f"{wd} ░░░░░░░░ —")

    lines.append(f"\n⏱ Всего: {_fmt_time(total_work)}")
    lines.append(f"🚨 Отвлечений: {total_dist}")
    lines.append(
        f"🔥 Стрик: {state.streak_days} дн. | "
        f"💼 Рабочих: {state.streak_workdays} дн."
    )
    if best_day:
        lines.append(f"\n🏆 Лучший день: {best_day}")
    return "\n".join(lines)


# ── bot class ─────────────────────────────────────────────────────────────────

class FocusBot:
    def __init__(self, token: str, chat_id: int, state: AppState,
                 todoist_token: str = ""):
        self._token          = token
        self._chat_id        = chat_id
        self._state          = state
        self._todoist_token  = todoist_token
        self._app            = Application.builder().token(token).build()
        self._break_task: asyncio.Task | None     = None
        self._planning_task: asyncio.Task | None  = None
        self._weekly_task: asyncio.Task | None    = None

        self._app.add_handler(CommandHandler("start",        self._cmd_start))
        self._app.add_handler(CommandHandler("achievements", self._cmd_achievements))
        self._app.add_handler(CallbackQueryHandler(self._on_button))

    # ── send helpers ──────────────────────────────────────────────────────────

    async def send(self, text: str, reply_markup=None, parse_mode="Markdown") -> Message:
        msg = await self._app.bot.send_message(
            chat_id=self._chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        self._state.add_message_id(msg.message_id)
        return msg

    async def send_menu(self, text: str, parse_mode="Markdown") -> Message:
        return await self.send(text, reply_markup=_keyboard_for_state(self._state),
                               parse_mode=parse_mode)

    async def clear_chat(self):
        ids = self._state.sent_message_ids
        if not ids:
            return
        max_id = max(ids)
        self._state.clear_message_ids()
        to_delete = list(range(max(1, max_id - 300), max_id + 1))
        for i in range(0, len(to_delete), 100):
            batch = to_delete[i:i + 100]
            try:
                await self._app.bot.delete_messages(chat_id=self._chat_id, message_ids=batch)
            except Exception:
                for mid in batch:
                    try:
                        await self._app.bot.delete_message(chat_id=self._chat_id, message_id=mid)
                    except Exception:
                        pass

    async def _notify_achievements(self, new_achs):
        for ach in new_achs:
            await self.send(format_achievement(ach))

    # ── command handlers ──────────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != self._chat_id:
            return
        msg = await update.message.reply_text(
            "👋 Привет! Я твой фокус-бот.",
            reply_markup=_keyboard_for_state(self._state),
        )
        self._state.add_message_id(msg.message_id)

    async def _cmd_achievements(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != self._chat_id:
            return
        from achievements import all_achievements_text
        await update.message.reply_text(
            f"🏅 *Твои ачивки*\n\n{all_achievements_text(self._state)}",
            parse_mode="Markdown",
        )

    async def _on_button(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if update.effective_chat.id != self._chat_id:
            return
        await query.answer()
        data = query.data

        if data == "start":
            is_new_day = self._state.day_started != date.today().isoformat()
            if is_new_day:
                await self.clear_chat()
            self._state.start_planning()
            left_min = int(self._state.planning_seconds_left() // 60)
            tasks = await _fetch_todoist_tasks(self._todoist_token)
            if tasks:
                task_lines = "\n".join(f"• {t}" for t in tasks)
                tasks_block = f"\n\n📌 *Задачи на сегодня:*\n{task_lines}"
            else:
                tasks_block = ""
            await self.send_menu(
                f"📋 *Время планирования!*\n"
                f"У тебя {left_min} минут чтобы составить план на день в Todoist.\n"
                f"Когда готов — нажми кнопку ниже."
                f"{tasks_block}"
            )
            self._schedule_planning_watcher()

        elif data == "ready" or data == "skip_plan":
            if not self._state.is_planning:
                return
            if self._planning_task and not self._planning_task.done():
                self._planning_task.cancel()
            self._state.start_working()
            await self.send_menu("🚀 Рабочий день начат! Удачи 💪")
            await self._notify_achievements(check_new_achievements(self._state))

        elif data == "break_short":
            if not self._state.is_working:
                return
            self._state.start_break(long=False)
            await self.send_menu("⏸ Перерыв 15 минут. Отдыхай!")
            self._schedule_break_watcher()

        elif data == "break_long":
            if not self._state.is_working:
                return
            self._state.start_break(long=True)
            await self.send_menu("🍽 Обед 60 минут. Приятного аппетита!")
            self._schedule_break_watcher()

        elif data == "return_break":
            if not self._state.is_on_break:
                return
            if self._break_task and not self._break_task.done():
                self._break_task.cancel()
            self._state.finish_break()
            await self.send_menu("🏃 Вернулся досрочно! Продолжаем 💪")

        elif data == "end":
            stats = self._state.end_day()
            todoist = await _fetch_todoist_stats(self._todoist_token)
            report = _build_end_of_day_report(stats, todoist, self._state)
            await self.send_menu(report)
            new_achs = check_new_achievements(self._state)
            await self._notify_achievements(new_achs)

    # ── watchers ──────────────────────────────────────────────────────────────

    def _schedule_planning_watcher(self):
        if self._planning_task and not self._planning_task.done():
            self._planning_task.cancel()
        self._planning_task = asyncio.create_task(
            self._state.watch_planning(self._on_planning_ended)
        )

    async def _on_planning_ended(self):
        await self.send_menu("⏱ Время планирования вышло. *Рабочий день начат!* 🚀")
        await self._notify_achievements(check_new_achievements(self._state))

    def _schedule_break_watcher(self):
        if self._break_task and not self._break_task.done():
            self._break_task.cancel()
        self._break_task = asyncio.create_task(
            self._state.watch_break(self._on_break_ended)
        )

    async def _on_break_ended(self):
        await self.send_menu("⏰ Перерыв закончился, возвращайся к работе! 💼")

    # ── weekly report scheduler ───────────────────────────────────────────────

    async def _weekly_report_loop(self):
        while True:
            now = datetime.now()
            if now.weekday() == 6 and now.hour == 20 and now.minute == 0:
                await self.send(_build_weekly_report(self._state), parse_mode="Markdown")
            await asyncio.sleep(60)

    # ── notifications (called from monitor) ──────────────────────────────────

    async def notify_idle(self, repeat: bool):
        if self._state.is_on_break or self._state.is_off or self._state.is_planning:
            return
        if repeat:
            await self.send("👀 Всё ещё здесь?")
        else:
            await self.send("😴 Ты куда пропал? Вернись к работе!")

    async def notify_distraction(self, app_name: str):
        if self._state.is_on_break or self._state.is_off or self._state.is_planning:
            return
        self._state.add_distraction()
        await self.send(f"🚨 Это {app_name}, не работа! Закрывай и фокусируйся.")

    # ── run ───────────────────────────────────────────────────────────────────

    async def run(self):
        await self._app.initialize()
        await self._app.start()
        self._weekly_task = asyncio.create_task(self._weekly_report_loop())
        if self._state.is_on_break:
            self._schedule_break_watcher()
        if self._state.is_planning:
            self._schedule_planning_watcher()
        await self._send_startup_message()
        await self._app.updater.start_polling(drop_pending_updates=True)

    async def _send_startup_message(self):
        if self._state.is_working:
            await self.send_menu(
                f"🔄 Бот перезапущен. Рабочий день уже идёт 💪\n"
                f"Перерывов: {self._state.short_breaks_today}/{MAX_SHORT_BREAKS}  |  "
                f"Обед: {'❌ использован' if self._state.long_breaks_today else '✅ доступен'}\n"
                f"{_streak_bar(self._state.streak_days)} {self._state.streak_days} дн."
            )
        elif self._state.is_planning:
            mins = int(self._state.planning_seconds_left() // 60)
            await self.send_menu(f"🔄 Бот перезапущен. Осталось {mins} мин на планирование 📋")
        elif self._state.is_on_break:
            mins = int(self._state.break_seconds_left() // 60)
            secs = int(self._state.break_seconds_left() % 60)
            await self.send_menu(f"🔄 Бот перезапущен. Ты на перерыве — осталось {mins}м {secs}с")
        else:
            await self.send_menu(
                f"🤖 Бот запущен. Нажми ▶️ чтобы начать день!\n"
                f"{_streak_bar(self._state.streak_days)} {self._state.streak_days} дн."
                if self._state.streak_days > 0
                else "🤖 Бот запущен. Нажми ▶️ чтобы начать день!"
            )

    async def stop(self):
        if self._weekly_task:
            self._weekly_task.cancel()
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()
