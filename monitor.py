import time
import asyncio
import platform
import subprocess
from pynput import mouse, keyboard

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

SYSTEM = platform.system()  # "Windows" / "Darwin" / "Linux"

IDLE_THRESHOLD   = 5 * 60
REPEAT_INTERVAL  = 1 * 60
WINDOW_CHECK_SEC = 5

DISTRACTING_APPS = [
    "youtube", "vk.com", "вконтакте",
    "instagram", "tiktok", "twitch",
    "netflix", "кинопоиск", "kinopoisk",
    "twitter", "x.com", "facebook",
]

# AppleScript для macOS: получает заголовок активной вкладки браузера
_MACOS_SCRIPT = """
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true
end tell
try
    if frontApp is "Google Chrome" then
        tell application "Google Chrome"
            return (get title of active tab of front window) & " [chrome]"
        end tell
    else if frontApp is "Safari" then
        tell application "Safari"
            return (get name of current tab of front window) & " [safari]"
        end tell
    else if frontApp is "Firefox" then
        tell application "Firefox"
            return (get name of front window) & " [firefox]"
        end tell
    else
        return frontApp
    end if
end try
return frontApp
"""


class ActivityMonitor:
    def __init__(self, state, on_idle, on_distraction):
        self._state          = state
        self._on_idle        = on_idle
        self._on_distraction = on_distraction
        self._last_activity  = time.time()
        self._idle_notified  = False
        self._last_repeat    = 0.0
        self._last_window    = ""

    # ── input listeners ───────────────────────────────────────────────────────

    def _touch(self):
        self._last_activity = time.time()
        self._idle_notified = False
        self._last_repeat   = 0.0

    def _start_listeners(self):
        mouse.Listener(
            on_move=lambda *_: self._touch(),
            on_click=lambda *_: self._touch(),
            on_scroll=lambda *_: self._touch(),
            daemon=True,
        ).start()
        keyboard.Listener(
            on_press=lambda _: self._touch(),
            daemon=True,
        ).start()

    # ── active window ─────────────────────────────────────────────────────────

    def _get_active_window_title(self) -> str:
        if SYSTEM == "Windows":
            if not HAS_WIN32:
                return ""
            try:
                hwnd = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(hwnd).lower()
            except Exception:
                return ""

        elif SYSTEM == "Darwin":
            try:
                result = subprocess.run(
                    ["osascript", "-e", _MACOS_SCRIPT],
                    capture_output=True, text=True, timeout=3
                )
                return result.stdout.strip().lower()
            except Exception:
                return ""

        return ""

    def _is_distracting(self, title: str) -> str | None:
        for app in DISTRACTING_APPS:
            if app in title:
                return app
        return None

    # ── main loop ─────────────────────────────────────────────────────────────

    async def run(self):
        self._start_listeners()
        window_tick = 0
        while True:
            await asyncio.sleep(1)

            if not self._state.is_working:
                self._last_window = ""
                continue

            now      = time.time()
            idle_sec = now - self._last_activity

            # --- idle check ---
            if idle_sec >= IDLE_THRESHOLD:
                if not self._idle_notified:
                    self._idle_notified = True
                    self._last_repeat   = now
                    await self._on_idle(repeat=False)
                elif now - self._last_repeat >= REPEAT_INTERVAL:
                    self._last_repeat = now
                    await self._on_idle(repeat=True)

            # --- window check ---
            window_tick += 1
            if window_tick >= WINDOW_CHECK_SEC:
                window_tick = 0
                title = self._get_active_window_title()
                if title:
                    distraction = self._is_distracting(title)
                    if distraction:
                        await self._on_distraction(distraction)
                    self._last_window = title
