import asyncio
import os
import platform
import sys
import traceback
import threading
from dotenv import load_dotenv
from state import AppState
from monitor import ActivityMonitor
from bot import FocusBot

load_dotenv()

BOT_TOKEN     = os.getenv("BOT_TOKEN")
CHAT_ID       = int(os.getenv("CHAT_ID"))
TODOIST_TOKEN = os.getenv("TODOIST_TOKEN", "")

SYSTEM = platform.system()

# ── Windows tray ───────────────────────────────────────────────────────────────
HAS_PYSTRAY = False
if SYSTEM == "Windows":
    try:
        import pystray
        from PIL import Image, ImageDraw
        HAS_PYSTRAY = True
    except ImportError:
        pass

# ── macOS menu bar ─────────────────────────────────────────────────────────────
HAS_RUMPS = False
if SYSTEM == "Darwin":
    try:
        import rumps
        HAS_RUMPS = True
    except ImportError:
        pass


def _make_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 62, 62], fill=(41, 182, 246, 255))
    pts = [(34, 6), (20, 34), (30, 34), (24, 58), (46, 26), (36, 26), (44, 6)]
    d.polygon(pts, fill="white")
    return img


def _start_windows_tray():
    if not HAS_PYSTRAY:
        return

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon(
        "FlowBot",
        _make_tray_image(),
        "FlowBot — работает",
        menu=pystray.Menu(
            pystray.MenuItem("FlowBot — работает", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Остановить бота", on_quit),
        ),
    )
    icon.run_detached()


async def _async_main():
    state   = AppState()
    bot     = FocusBot(
        token         = BOT_TOKEN,
        chat_id       = CHAT_ID,
        state         = state,
        todoist_token = TODOIST_TOKEN,
    )
    monitor = ActivityMonitor(
        state          = state,
        on_idle        = bot.notify_idle,
        on_distraction = bot.notify_distraction,
    )
    await bot.run()
    await monitor.run()


def _run_async():
    try:
        asyncio.run(_async_main())
    except Exception:
        log_path = os.path.join(os.path.dirname(__file__), "error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        os._exit(1)


if __name__ == "__main__":
    if SYSTEM == "Darwin" and HAS_RUMPS:
        # macOS: asyncio в фоновом потоке, rumps занимает главный поток
        t = threading.Thread(target=_run_async, daemon=True)
        t.start()

        class _MenuBarApp(rumps.App):
            def __init__(self):
                super().__init__("⚡", quit_button=None)
                self.menu = [
                    rumps.MenuItem("FlowBot — работает"),
                    None,
                    rumps.MenuItem("Остановить бота", callback=self._quit),
                ]

            def _quit(self, _):
                os._exit(0)

        _MenuBarApp().run()

    else:
        # Windows: иконка в трей, asyncio в главном потоке
        if SYSTEM == "Windows":
            _start_windows_tray()
        try:
            asyncio.run(_async_main())
        except Exception:
            log_path = os.path.join(os.path.dirname(__file__), "error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
            raise
