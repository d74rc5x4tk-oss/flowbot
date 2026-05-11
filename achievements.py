"""Achievements — long-term milestones."""

from dataclasses import dataclass
from typing import Callable
from i18n import t


@dataclass
class Achievement:
    id: str
    emoji: str
    title: dict   # {"ru": ..., "en": ...}
    description: dict
    check: Callable  # (state) -> bool


ALL_ACHIEVEMENTS = [
    Achievement(
        id="first_day", emoji="🌱",
        title={"ru": "Первый шаг",       "en": "First step"},
        description={"ru": "Начал первый рабочий день", "en": "Started your first work day"},
        check=lambda s: s.streak_days >= 1,
    ),
    Achievement(
        id="streak_3", emoji="🔥",
        title={"ru": "Огонь",            "en": "On fire"},
        description={"ru": "3 дня подряд",              "en": "3 days in a row"},
        check=lambda s: s.streak_days >= 3,
    ),
    Achievement(
        id="streak_7", emoji="⚡",
        title={"ru": "В ритме",          "en": "In the zone"},
        description={"ru": "7 дней подряд",             "en": "7 days in a row"},
        check=lambda s: s.streak_days >= 7,
    ),
    Achievement(
        id="streak_30", emoji="🏆",
        title={"ru": "Чемпион",          "en": "Champion"},
        description={"ru": "30 дней подряд",            "en": "30 days in a row"},
        check=lambda s: s.streak_days >= 30,
    ),
    Achievement(
        id="streak_365", emoji="👑",
        title={"ru": "Легенда",          "en": "Legend"},
        description={"ru": "365 дней подряд",           "en": "365 days in a row"},
        check=lambda s: s.streak_days >= 365,
    ),
    Achievement(
        id="workdays_5", emoji="💼",
        title={"ru": "Рабочая неделя",   "en": "Full work week"},
        description={"ru": "5 рабочих дней Пн–Пт подряд", "en": "5 workdays Mon–Fri in a row"},
        check=lambda s: s.streak_workdays >= 5,
    ),
    Achievement(
        id="workdays_20", emoji="🎖",
        title={"ru": "Рабочий месяц",    "en": "Full work month"},
        description={"ru": "20 рабочих дней Пн–Пт подряд", "en": "20 workdays Mon–Fri in a row"},
        check=lambda s: s.streak_workdays >= 20,
    ),
    Achievement(
        id="clean_3", emoji="👁",
        title={"ru": "Орёл",             "en": "Eagle eye"},
        description={"ru": "3 дня без единого отвлечения",  "en": "3 days without a single distraction"},
        check=lambda s: s.streak_clean >= 3,
    ),
    Achievement(
        id="clean_7", emoji="🎯",
        title={"ru": "Снайпер",          "en": "Sniper"},
        description={"ru": "7 дней без единого отвлечения",  "en": "7 days without a single distraction"},
        check=lambda s: s.streak_clean >= 7,
    ),
    Achievement(
        id="clean_30", emoji="🧘",
        title={"ru": "Дзен",             "en": "Zen"},
        description={"ru": "30 дней без единого отвлечения", "en": "30 days without a single distraction"},
        check=lambda s: s.streak_clean >= 30,
    ),
]

_BY_ID = {a.id: a for a in ALL_ACHIEVEMENTS}


def check_new_achievements(state) -> list[Achievement]:
    earned = []
    for ach in ALL_ACHIEVEMENTS:
        if ach.id not in state.achievements and ach.check(state):
            state.achievements.append(ach.id)
            earned.append(ach)
    if earned:
        state.save()
    return earned


def format_achievement(ach: Achievement, lang: str = "ru") -> str:
    title = ach.title.get(lang) or ach.title.get("en", "")
    desc  = ach.description.get(lang) or ach.description.get("en", "")
    return t("ach_new", lang, emoji=ach.emoji, title=title, desc=desc)


def all_achievements_text(state, lang: str = "ru") -> str:
    if not state.achievements:
        return t("ach_none", lang)
    lines = []
    for ach_id in state.achievements:
        if ach_id in _BY_ID:
            a     = _BY_ID[ach_id]
            title = a.title.get(lang) or a.title.get("en", "")
            desc  = a.description.get(lang) or a.description.get("en", "")
            lines.append(f"{a.emoji} {title} — {desc}")
    return "\n".join(lines)
