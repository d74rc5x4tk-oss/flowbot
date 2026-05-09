import asyncio
import os
from dotenv import load_dotenv
from state import AppState
from monitor import ActivityMonitor
from bot import FocusBot

load_dotenv()

BOT_TOKEN      = os.getenv("BOT_TOKEN")
CHAT_ID        = int(os.getenv("CHAT_ID"))
TODOIST_TOKEN  = os.getenv("TODOIST_TOKEN", "")


async def main():
    state = AppState()
    bot   = FocusBot(
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


if __name__ == "__main__":
    asyncio.run(main())
