import asyncio
import os
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from state import AppState, MAX_SHORT_BREAKS
from achievements import check_new_achievements, format_achievement
from i18n import t, detect_lang

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# ── keyboards ─────────────────────────────────────────────────────────────────

def _keyboard_for_state(state: AppState) -> InlineKeyboardMarkup:
    lang = state.language
    if state.is_off:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_start", lang), callback_data="start")],
        ])
    if state.is_planning:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_ready", lang), callback_data="ready")],
            [InlineKeyboardButton(t("btn_skip_plan", lang), callback_data="skip_plan")],
        ])
    if state.is_on_break:
        rows = []
        if state.can_extend_break:
            left = MAX_SHORT_BREAKS - state.short_breaks_today
            rows.append([InlineKeyboardButton(
                t("btn_extend_break", lang, left=left), callback_data="extend_break"
            )])
        rows.append([InlineKeyboardButton(t("btn_return_break", lang), callback_data="return_break")])
        return InlineKeyboardMarkup(rows)
    # working
    break_row = []
    if state.can_short_break:
        left = MAX_SHORT_BREAKS - state.short_breaks_today
        break_row.append(InlineKeyboardButton(
            t("btn_break_short", lang, left=left), callback_data="break_short"
        ))
    if state.can_long_break:
        break_row.append(InlineKeyboardButton(t("btn_lunch", lang), callback_data="break_long"))
    rows = []
    if break_row:
        rows.append(break_row)
    rows.append([InlineKeyboardButton(t("btn_end_day", lang), callback_data="end")])
    return InlineKeyboardMarkup(rows)


# ── formatting helpers ────────────────────────────────────────────────────────

def _fmt_time(seconds: int, lang: str = "ru") -> str:
    h, m = divmod(seconds // 60, 60)
    if h:
        return t("time_hm", lang, h=h, m=m)
    return t("time_m", lang, m=m)


def _streak_bar(n: int) -> str:
    return "🔥" * min(n, 7) + (f" ×{n}" if n > 7 else "")


async def _fetch_todoist_tasks(token: str) -> list[str]:
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
            return [item["content"] for item in results]
    except Exception:
        return []


async def _fetch_todoist_stats(token: str) -> dict | None:
    if not HAS_HTTPX or not token:
        return None
    today = date.today().isoformat()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.todoist.com/api/v1/tasks",
                headers=headers,
                params={"filter": "today | overdue"},
            )
            active = len(r.json().get("results", [])) if r.status_code == 200 else 0

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
                              incomplete_tasks: list[str],
                              state: AppState) -> str:
    lang      = state.language
    work_str  = _fmt_time(stats["work_seconds"], lang)
    break_str = _fmt_time(stats["break_seconds"], lang)
    dist      = stats["distractions"]

    focus_pct = max(0, 1 - dist / 10)
    score = focus_pct * 40
    work_pct = min(1, stats["work_seconds"] / (8 * 3600))
    score += work_pct * 20

    if todoist is None:
        score += 20
        todoist_line = t("report_todoist_no", lang) + "\n"
    elif todoist["total"] == 0:
        score += 20
        todoist_line = t("report_todoist_empty", lang) + "\n"
    else:
        t_pct = todoist["completed"] / todoist["total"]
        score += t_pct * 40
        todoist_line = t("report_todoist", lang,
                         done=todoist["completed"],
                         total=todoist["total"],
                         pct=int(t_pct * 100)) + "\n"

    score = min(10, round(score / 10, 1))

    work_hours = stats["work_seconds"] / 3600
    if work_hours >= 9:
        grade = t("grade_galley", lang)
    elif work_hours >= 6:
        grade = t("grade_worker", lang)
    elif work_hours >= 3:
        grade = t("grade_growing", lang)
    else:
        grade = t("grade_lazy", lang)

    streak_line = t("report_streaks", lang,
                    d=state.streak_days,
                    c=state.streak_clean,
                    w=state.streak_workdays)

    overdue_block = ""
    if incomplete_tasks:
        task_lines   = "\n".join(f"• {item}" for item in incomplete_tasks)
        overdue_block = f"\n\n{t('report_overdue', lang)}\n{task_lines}"

    return (
        f"{t('report_header', lang)}\n\n"
        f"{t('report_work', lang, t=work_str)}\n"
        f"{t('report_break', lang, t=break_str)}\n"
        f"{t('report_dist', lang, n=dist)}\n"
        f"{todoist_line}\n"
        f"{streak_line}\n\n"
        f"{t('report_score', lang, score=score, grade=grade)}"
        f"{overdue_block}"
    )


def _build_weekly_report(state: AppState) -> str:
    lang     = state.language
    today    = date.today()
    weekdays = t("weekdays", lang)
    lines    = [t("week_header", lang) + "\n"]
    total_work = 0
    total_dist = 0
    best_day   = None
    best_work  = 0

    for i in range(6, -1, -1):
        d  = today - timedelta(days=i)
        ds = d.isoformat()
        wd = weekdays[d.weekday()]
        if ds in state.daily_stats:
            st    = state.daily_stats[ds]
            w     = st["work_seconds"]
            total_work += w
            total_dist += st["distractions"]
            hours = w / 3600
            bar   = "█" * int(hours) + "░" * max(0, 8 - int(hours))
            lines.append(f"{wd} {bar} {_fmt_time(w, lang)}")
            if w > best_work:
                best_work = w
                best_day  = wd
        else:
            lines.append(f"{wd} ░░░░░░░░ —")

    lines.append(f"\n{t('week_total', lang, t=_fmt_time(total_work, lang))}")
    lines.append(t("week_dist", lang, n=total_dist))
    lines.append(t("week_streaks", lang, d=state.streak_days, w=state.streak_workdays))
    if best_day:
        lines.append(f"\n{t('week_best', lang, day=best_day)}")
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

    def _sync_lang(self, update: Update):
        lang_code = update.effective_user.language_code if update.effective_user else None
        lang = detect_lang(lang_code)
        if lang != self._state.language:
            self._state.language = lang
            self._state.save()

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
        lang = self._state.language
        for ach in new_achs:
            await self.send(format_achievement(ach, lang))

    # ── command handlers ──────────────────────────────────────────────────────

    async def _cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != self._chat_id:
            return
        self._sync_lang(update)
        lang = self._state.language
        msg = await update.message.reply_text(
            t("welcome", lang),
            reply_markup=_keyboard_for_state(self._state),
        )
        self._state.add_message_id(msg.message_id)

    async def _cmd_achievements(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != self._chat_id:
            return
        self._sync_lang(update)
        lang = self._state.language
        from achievements import all_achievements_text
        await update.message.reply_text(
            f"{t('ach_header', lang)}\n\n{all_achievements_text(self._state, lang)}",
            parse_mode="Markdown",
        )

    async def _on_button(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if update.effective_chat.id != self._chat_id:
            return
        self._sync_lang(update)
        lang = self._state.language
        await query.answer()
        data = query.data

        if data == "start":
            is_new_day = self._state.session_started_date != date.today().isoformat()
            if is_new_day:
                await self.clear_chat()
            self._state.start_planning()
            left_min = int(self._state.planning_seconds_left() // 60)
            tasks = await _fetch_todoist_tasks(self._todoist_token)
            if tasks:
                task_lines  = "\n".join(f"• {item}" for item in tasks)
                tasks_block = f"\n\n{t('planning_tasks', lang)}\n{task_lines}"
            else:
                tasks_block = ""
            await self.send_menu(t("planning_start", lang, mins=left_min) + tasks_block)
            self._schedule_planning_watcher()

        elif data in ("ready", "skip_plan"):
            if not self._state.is_planning:
                return
            if self._planning_task and not self._planning_task.done():
                self._planning_task.cancel()
            self._state.start_working()
            await self.send_menu(t("day_started", lang))
            await self._notify_achievements(check_new_achievements(self._state))

        elif data == "break_short":
            if not self._state.is_working:
                return
            self._state.start_break(long=False)
            await self.send_menu(t("break_short_start", lang))
            self._schedule_break_watcher()

        elif data == "break_long":
            if not self._state.is_working:
                return
            self._state.start_break(long=True)
            await self.send_menu(t("break_long_start", lang))
            self._schedule_break_watcher()

        elif data == "extend_break":
            if not self._state.can_extend_break:
                return
            self._state.extend_break()
            if self._break_task and not self._break_task.done():
                self._break_task.cancel()
            self._schedule_break_watcher()
            left = MAX_SHORT_BREAKS - self._state.short_breaks_today
            total_min = self._state.break_duration // 60
            await self.send_menu(t("break_extended", lang, left=left, total=total_min))

        elif data == "return_break":
            if not self._state.is_on_break:
                return
            if self._break_task and not self._break_task.done():
                self._break_task.cancel()
            self._state.finish_break()
            await self.send_menu(t("return_early", lang))

        elif data == "end":
            incomplete = await _fetch_todoist_tasks(self._todoist_token)
            stats      = self._state.end_day()
            todoist    = await _fetch_todoist_stats(self._todoist_token)
            report     = _build_end_of_day_report(stats, todoist, incomplete, self._state)
            await self.send_menu(report)
            await self._notify_achievements(check_new_achievements(self._state))

    # ── watchers ──────────────────────────────────────────────────────────────

    def _schedule_planning_watcher(self):
        if self._planning_task and not self._planning_task.done():
            self._planning_task.cancel()
        self._planning_task = asyncio.create_task(
            self._state.watch_planning(self._on_planning_ended)
        )

    async def _on_planning_ended(self):
        await self.send_menu(t("planning_ended", self._state.language))
        await self._notify_achievements(check_new_achievements(self._state))

    def _schedule_break_watcher(self):
        if self._break_task and not self._break_task.done():
            self._break_task.cancel()
        self._break_task = asyncio.create_task(
            self._state.watch_break(self._on_break_ended)
        )

    async def _on_break_ended(self):
        await self.send_menu(t("break_ended", self._state.language))

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
        lang = self._state.language
        await self.send(t("idle_repeat" if repeat else "idle_first", lang))

    async def notify_distraction(self, app_name: str):
        if self._state.is_on_break or self._state.is_off or self._state.is_planning:
            return
        self._state.add_distraction()
        await self.send(t("distraction", self._state.language, app=app_name))

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
        lang  = self._state.language
        today = date.today().isoformat()
        if self._state.is_working:
            lunch_str = t("lunch_used" if self._state.long_breaks_today else "lunch_avail", lang)
            await self.send_menu(
                t("restart_working", lang,
                  sb=self._state.short_breaks_today,
                  max_sb=MAX_SHORT_BREAKS,
                  lunch=lunch_str,
                  streak_bar=_streak_bar(self._state.streak_days),
                  streak=self._state.streak_days)
            )
        elif self._state.is_planning:
            mins = int(self._state.planning_seconds_left() // 60)
            await self.send_menu(t("restart_planning", lang, mins=mins))
        elif self._state.is_on_break:
            mins = int(self._state.break_seconds_left() // 60)
            secs = int(self._state.break_seconds_left() % 60)
            await self.send_menu(t("restart_break", lang, mins=mins, secs=secs))
        else:
            # Не отправлять повторно если уже отправляли сегодня
            # (защита от второго компьютера, запускающего бот в середине дня)
            if self._state.startup_notified_date == today:
                return
            self._state.startup_notified_date = today
            self._state.save()
            text = t("start_day_prompt", lang)
            if self._state.streak_days > 0:
                text += f"\n{_streak_bar(self._state.streak_days)} {self._state.streak_days} {t('days_abbr', lang)}"
            await self.send_menu(text)

    async def stop(self):
        if self._weekly_task:
            self._weekly_task.cancel()
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()
