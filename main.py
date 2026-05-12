import asyncio
import os
import platform
import subprocess
import sys
import traceback
import threading
from dotenv import load_dotenv
from state import AppState
from monitor import ActivityMonitor
from bot import FocusBot
from i18n import t as _t, os_lang

load_dotenv()

BOT_TOKEN     = os.getenv("BOT_TOKEN")
CHAT_ID       = int(os.getenv("CHAT_ID"))
TODOIST_TOKEN = os.getenv("TODOIST_TOKEN", "")

SYSTEM = platform.system()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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


def _kill_sibling_instances():
    """Убивает только python-процессы, запущенные из нашей папки (main.py)."""
    current_pid = os.getpid()
    our_main = os.path.join(SCRIPT_DIR, "main.py").replace('\\', '/').lower()
    try:
        result = subprocess.run(
            ['wmic', 'process', 'get', 'name,processid,commandline', '/format:csv'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            norm = line.replace('\\', '/').lower()
            # Только python-процессы с точным путём к нашему main.py
            if 'python' not in norm or our_main not in norm:
                continue
            parts = line.strip().split(',')
            try:
                pid = int(parts[-1].strip())
                if pid != current_pid and pid > 0:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                                   capture_output=True, timeout=3)
            except (ValueError, subprocess.TimeoutExpired):
                pass
    except Exception:
        pass


def _restart_bot():
    """Убивает все экземпляры, запускает один новый и завершает текущий."""
    def do_restart():
        import time
        _kill_sibling_instances()
        time.sleep(1)  # дать Telegram время закрыть соединение
        kwargs = {"cwd": SCRIPT_DIR}
        if SYSTEM == "Windows":
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, "main.py")], **kwargs)
        os._exit(0)
    threading.Thread(target=do_restart, daemon=True).start()


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

    def on_restart(icon, item):
        _restart_bot()

    def on_quit(icon, item):
        icon.stop()
        _kill_sibling_instances()
        os._exit(0)

    lang = os_lang()
    icon = pystray.Icon(
        "FlowBot",
        _make_tray_image(),
        _t("tray_running", lang),
        menu=pystray.Menu(
            pystray.MenuItem(_t("tray_running", lang), None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_t("tray_restart", lang), on_restart),
            pystray.MenuItem(_t("tray_stop", lang), on_quit),
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
        log_path = os.path.join(SCRIPT_DIR, "error.log")
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
                lang = os_lang()
                self.menu = [
                    rumps.MenuItem(_t("tray_running", lang)),
                    None,
                    rumps.MenuItem(_t("tray_restart", lang), callback=self._restart),
                    rumps.MenuItem(_t("tray_stop", lang), callback=self._quit),
                ]

            def _restart(self, _):
                _restart_bot()

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
            log_path = os.path.join(SCRIPT_DIR, "error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
            raise
