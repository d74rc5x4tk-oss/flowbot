import json
import asyncio
import time as _time
from datetime import date, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

BREAK_SHORT      = 15 * 60
BREAK_LONG       = 60 * 60
MAX_SHORT_BREAKS = 4
MAX_LONG_BREAKS  = 1
PLANNING_MINUTES = 10


# ── streak helpers ────────────────────────────────────────────────────────────

def _streak_continues(last_str: str, today: date) -> bool:
    """Стрик продолжается если разрыв между датами — только выходные."""
    if not last_str:
        return False
    last = date.fromisoformat(last_str)
    delta = (today - last).days
    if delta <= 0:
        return True
    if delta == 1:
        return True
    between = [last + timedelta(days=i) for i in range(1, delta)]
    return all(d.weekday() >= 5 for d in between)


def _prev_workday(d: date) -> date:
    prev = d - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


def _workday_streak_continues(last_str: str, today: date) -> bool:
    """Рабочий стрик (Пн–Пт): продолжается если предыдущий рабочий день отработан."""
    if not last_str:
        return False
    last = date.fromisoformat(last_str)
    prev = _prev_workday(today)
    return last >= prev


class AppState:
    def __init__(self):
        # Режим работы
        self.mode = "off"                     # off | planning | working | break
        self.break_end: float | None = None
        self.break_type: str | None = None
        self.planning_end_time: float | None = None

        # Счётчики перерывов за день
        self.short_breaks_today: int = 0
        self.long_breaks_today: int = 0
        self.break_duration: int = 0

        # Стрики
        self.streak_days: int = 0             # календарные дни подряд
        self.streak_clean: int = 0            # дни без отвлечений подряд
        self.streak_workdays: int = 0         # рабочие дни Пн–Пт подряд
        self.last_work_date: str = ""
        self.last_clean_date: str = ""
        self.last_workday_date: str = ""

        # Статистика за день
        self.distractions_today: int = 0
        self._work_segment_start: float = 0.0
        self.total_work_seconds: int = 0
        self.total_break_seconds: int = 0

        # Мета
        self.day_started: str | None = None
        self.sent_message_ids: list[int] = []
        self.achievements: list[str] = []
        self.daily_stats: dict = {}           # date_str → {work_sec, break_sec, distractions, score}
        self.language: str = "ru"
        self.startup_notified_date: str = ""
        self.session_started_date: str = ""

        self._load()

    # ── persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.mode                = d.get("mode", "off")
                self.break_end           = d.get("break_end")
                self.break_type          = d.get("break_type")
                self.planning_end_time   = d.get("planning_end_time")
                self.short_breaks_today  = d.get("short_breaks_today", 0)
                self.long_breaks_today   = d.get("long_breaks_today", 0)
                self.break_duration      = d.get("break_duration", 0)
                self.streak_days         = d.get("streak_days", 0)
                self.streak_clean        = d.get("streak_clean", 0)
                self.streak_workdays     = d.get("streak_workdays", 0)
                self.last_work_date      = d.get("last_work_date", "")
                self.last_clean_date     = d.get("last_clean_date", "")
                self.last_workday_date   = d.get("last_workday_date", "")
                self.distractions_today  = d.get("distractions_today", 0)
                self.total_work_seconds  = d.get("total_work_seconds", 0)
                self.total_break_seconds = d.get("total_break_seconds", 0)
                self.day_started         = d.get("day_started")
                self.sent_message_ids    = d.get("sent_message_ids", [])
                self.achievements        = d.get("achievements", [])
                self.daily_stats         = d.get("daily_stats", {})
                self.language                = d.get("language", "ru")
                self.startup_notified_date   = d.get("startup_notified_date", "")
                self.session_started_date    = d.get("session_started_date", "")
                if self.mode in ("planning", "working"):
                    self._work_segment_start = _time.time()
                self._midnight_reset()
            except Exception:
                pass

    def save(self):
        STATE_FILE.write_text(
            json.dumps({
                "mode":               self.mode,
                "break_end":          self.break_end,
                "break_type":         self.break_type,
                "planning_end_time":  self.planning_end_time,
                "short_breaks_today": self.short_breaks_today,
                "long_breaks_today":  self.long_breaks_today,
                "break_duration":     self.break_duration,
                "streak_days":        self.streak_days,
                "streak_clean":       self.streak_clean,
                "streak_workdays":    self.streak_workdays,
                "last_work_date":     self.last_work_date,
                "last_clean_date":    self.last_clean_date,
                "last_workday_date":  self.last_workday_date,
                "distractions_today": self.distractions_today,
                "total_work_seconds": self.total_work_seconds,
                "total_break_seconds":self.total_break_seconds,
                "day_started":        self.day_started,
                "sent_message_ids":   self.sent_message_ids,
                "achievements":       self.achievements,
                "daily_stats":        self.daily_stats,
                "language":                self.language,
                "startup_notified_date":   self.startup_notified_date,
                "session_started_date":    self.session_started_date,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── midnight reset ────────────────────────────────────────────────────────

    def _midnight_reset(self):
        today = date.today().isoformat()
        if self.day_started and self.day_started != today:
            self.mode                = "off"
            self.break_end           = None
            self.break_type          = None
            self.planning_end_time   = None
            self.short_breaks_today  = 0
            self.long_breaks_today   = 0
            self.distractions_today  = 0
            self.total_work_seconds  = 0
            self.total_break_seconds = 0
        self.day_started = today
        self.save()

    # ── streak update ─────────────────────────────────────────────────────────

    def _update_streaks_on_start(self):
        today = date.today()
        today_str = today.isoformat()

        # Календарный стрик (выходные не ломают)
        if _streak_continues(self.last_work_date, today):
            if self.last_work_date != today_str:
                self.streak_days += 1
        else:
            self.streak_days = 1
        self.last_work_date = today_str

        # Рабочий стрик Пн–Пт
        if today.weekday() < 5:
            if _workday_streak_continues(self.last_workday_date, today):
                if self.last_workday_date != today_str:
                    self.streak_workdays += 1
            else:
                self.streak_workdays = 1
            self.last_workday_date = today_str

    def _update_clean_streak(self):
        """Вызывается при завершении дня. Если 0 отвлечений — чистый стрик растёт."""
        today = date.today()
        today_str = today.isoformat()
        if self.distractions_today == 0:
            if _streak_continues(self.last_clean_date, today):
                if self.last_clean_date != today_str:
                    self.streak_clean += 1
            else:
                self.streak_clean = 1
            self.last_clean_date = today_str
        else:
            self.streak_clean = 0

    # ── message id tracking ───────────────────────────────────────────────────

    def add_message_id(self, mid: int):
        self.sent_message_ids.append(mid)
        self.save()

    def clear_message_ids(self):
        self.sent_message_ids = []
        self.save()

    # ── work time tracking ────────────────────────────────────────────────────

    def _flush_work_segment(self):
        if self._work_segment_start > 0:
            self.total_work_seconds += int(_time.time() - self._work_segment_start)
        self._work_segment_start = 0.0

    def _flush_break_segment(self):
        if self.break_end is not None:
            elapsed = self.break_duration or (BREAK_LONG if self.break_type == "long" else BREAK_SHORT)
            left = self.break_seconds_left()
            self.total_break_seconds += int(elapsed - left)

    # ── actions ───────────────────────────────────────────────────────────────

    def start_planning(self):
        self._midnight_reset()
        self._update_streaks_on_start()
        self.mode                 = "planning"
        self.planning_end_time    = _time.time() + PLANNING_MINUTES * 60
        self._work_segment_start  = 0.0
        self.session_started_date = date.today().isoformat()
        self.save()

    def start_working(self):
        """Переход из планирования в рабочий режим."""
        self.mode              = "working"
        self.planning_end_time = None
        self._work_segment_start = _time.time()
        self.save()

    def start_day(self):
        """Обратная совместимость — сразу рабочий режим без планирования."""
        self._midnight_reset()
        self._update_streaks_on_start()
        self.mode                 = "working"
        self.planning_end_time    = None
        self._work_segment_start  = _time.time()
        self.session_started_date = date.today().isoformat()
        self.save()

    def end_day(self) -> dict:
        """Завершить день. Возвращает статистику за день."""
        self._flush_work_segment()
        self._flush_break_segment()
        self._update_clean_streak()

        stats = {
            "work_seconds":   self.total_work_seconds,
            "break_seconds":  self.total_break_seconds,
            "distractions":   self.distractions_today,
            "short_breaks":   self.short_breaks_today,
            "long_breaks":    self.long_breaks_today,
        }
        # Сохраняем в историю (храним последние 14 дней)
        today_str = date.today().isoformat()
        self.daily_stats[today_str] = stats
        cutoff = (date.today() - timedelta(days=14)).isoformat()
        self.daily_stats = {k: v for k, v in self.daily_stats.items() if k >= cutoff}

        self.mode               = "off"
        self.break_end          = None
        self.break_type         = None
        self.planning_end_time  = None
        self.save()
        return stats

    def start_break(self, long: bool = False):
        self._flush_work_segment()
        duration            = BREAK_LONG if long else BREAK_SHORT
        self.mode           = "break"
        self.break_end      = _time.time() + duration
        self.break_type     = "long" if long else "short"
        self.break_duration = duration
        if long:
            self.long_breaks_today += 1
        else:
            self.short_breaks_today += 1
        self.save()
        return duration

    def extend_break(self):
        """Продлить короткий перерыв ещё на 15 минут, потратив ещё один слот."""
        self.break_end = (self.break_end or _time.time()) + BREAK_SHORT
        self.break_duration += BREAK_SHORT
        self.short_breaks_today += 1
        self.save()

    def finish_break(self):
        self._flush_break_segment()
        self.mode           = "working"
        self.break_end      = None
        self.break_type     = None
        self.break_duration = 0
        self._work_segment_start = _time.time()
        self.save()

    def add_distraction(self):
        self.distractions_today += 1
        self.save()

    # ── helpers ───────────────────────────────────────────────────────────────

    @property
    def is_planning(self) -> bool:
        return self.mode == "planning"

    @property
    def is_working(self) -> bool:
        return self.mode == "working"

    @property
    def is_on_break(self) -> bool:
        return self.mode == "break"

    @property
    def is_off(self) -> bool:
        return self.mode == "off"

    @property
    def can_short_break(self) -> bool:
        return self.short_breaks_today < MAX_SHORT_BREAKS

    @property
    def can_long_break(self) -> bool:
        return self.long_breaks_today < MAX_LONG_BREAKS

    @property
    def can_extend_break(self) -> bool:
        return self.is_on_break and self.break_type == "short" and self.can_short_break

    def break_seconds_left(self) -> float:
        if self.break_end is None:
            return 0
        return max(0, self.break_end - _time.time())

    def planning_seconds_left(self) -> float:
        if self.planning_end_time is None:
            return 0
        return max(0, self.planning_end_time - _time.time())

    def get_work_duration(self) -> int:
        """Текущее рабочее время в секундах (включая незавершённый сегмент)."""
        extra = int(_time.time() - self._work_segment_start) if self._work_segment_start > 0 else 0
        return self.total_work_seconds + extra

    async def watch_break(self, on_break_end):
        while self.is_on_break:
            left = self.break_seconds_left()
            if left <= 0:
                self.finish_break()
                await on_break_end()
                return
            await asyncio.sleep(min(left, 10))

    async def watch_planning(self, on_planning_end):
        while self.is_planning:
            left = self.planning_seconds_left()
            if left <= 0:
                self.start_working()
                await on_planning_end()
                return
            await asyncio.sleep(min(left, 10))
