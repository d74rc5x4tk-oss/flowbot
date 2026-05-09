"""Ачивки — долгосрочные достижения."""

from dataclasses import dataclass
from typing import Callable


@dataclass
class Achievement:
    id: str
    emoji: str
    title: str
    description: str
    check: Callable  # (state) -> bool


ALL_ACHIEVEMENTS = [
    Achievement(
        id="first_day",
        emoji="🌱",
        title="Первый шаг",
        description="Начал первый рабочий день",
        check=lambda s: s.streak_days >= 1,
    ),
    Achievement(
        id="streak_3",
        emoji="🔥",
        title="Огонь",
        description="3 дня подряд",
        check=lambda s: s.streak_days >= 3,
    ),
    Achievement(
        id="streak_7",
        emoji="⚡",
        title="В ритме",
        description="7 дней подряд",
        check=lambda s: s.streak_days >= 7,
    ),
    Achievement(
        id="streak_30",
        emoji="🏆",
        title="Чемпион",
        description="30 дней подряд",
        check=lambda s: s.streak_days >= 30,
    ),
    Achievement(
        id="streak_365",
        emoji="👑",
        title="Легенда",
        description="365 дней подряд",
        check=lambda s: s.streak_days >= 365,
    ),
    Achievement(
        id="workdays_5",
        emoji="💼",
        title="Рабочая неделя",
        description="5 рабочих дней Пн–Пт подряд",
        check=lambda s: s.streak_workdays >= 5,
    ),
    Achievement(
        id="workdays_20",
        emoji="🎖",
        title="Рабочий месяц",
        description="20 рабочих дней Пн–Пт подряд",
        check=lambda s: s.streak_workdays >= 20,
    ),
    Achievement(
        id="clean_3",
        emoji="👁",
        title="Орёл",
        description="3 дня без единого отвлечения",
        check=lambda s: s.streak_clean >= 3,
    ),
    Achievement(
        id="clean_7",
        emoji="🎯",
        title="Снайпер",
        description="7 дней без единого отвлечения",
        check=lambda s: s.streak_clean >= 7,
    ),
    Achievement(
        id="clean_30",
        emoji="🧘",
        title="Дзен",
        description="30 дней без единого отвлечения",
        check=lambda s: s.streak_clean >= 30,
    ),
]

_BY_ID = {a.id: a for a in ALL_ACHIEVEMENTS}


def check_new_achievements(state) -> list[Achievement]:
    """Возвращает список только что заработанных ачивок."""
    earned = []
    for ach in ALL_ACHIEVEMENTS:
        if ach.id not in state.achievements and ach.check(state):
            state.achievements.append(ach.id)
            earned.append(ach)
    if earned:
        state.save()
    return earned


def format_achievement(ach: Achievement) -> str:
    return (
        f"🏅 Новая ачивка!\n"
        f"{ach.emoji} *{ach.title}*\n"
        f"_{ach.description}_"
    )


def all_achievements_text(state) -> str:
    if not state.achievements:
        return "Пока нет ачивок. Начни работать! 💪"
    lines = []
    for ach_id in state.achievements:
        if ach_id in _BY_ID:
            a = _BY_ID[ach_id]
            lines.append(f"{a.emoji} {a.title} — {a.description}")
    return "\n".join(lines)
