"""
Reminder scheduler.

This is what was missing before: reminders were only ever *displayed* on
request (/reminders), never actually pushed to the user when their time
arrived. This module runs a lightweight background loop, inside the same
asyncio event loop as the bot's polling, that wakes up periodically, finds
every reminder whose time has come, sends it, and rolls recurring ones
forward to their next occurrence.

No extra dependencies (Celery, APScheduler, ...) needed -- for a personal-use
bot, a plain `asyncio` loop checking every CHECK_INTERVAL_SECONDS is simple,
robust, and easy to reason about. If this ever needs to run across multiple
processes/workers, swap this for Celery beat + a periodic task that calls
the same `get_due_reminders` / `advance_or_deactivate_reminder` helpers.
"""
import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from .utils import get_due_reminders, advance_or_deactivate_reminder, esc

logger = logging.getLogger("telegram_bot.scheduler")

CHECK_INTERVAL_SECONDS = 20


async def reminder_loop(bot: Bot):
    logger.info("⏰ Reminder scheduler started (checking every %ss)", CHECK_INTERVAL_SECONDS)
    while True:
        try:
            await _fire_due_reminders(bot)
        except Exception:
            logger.exception("Error while checking due reminders")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _fire_due_reminders(bot: Bot):
    due = await get_due_reminders()
    for reminder, chat_id in due:
        text = f"🔔 <b>یادآوری!</b>\n\n{esc(reminder.title)}"
        if reminder.description:
            text += f"\n{esc(reminder.description)}"
        try:
            await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        except TelegramAPIError:
            logger.exception("Failed to deliver reminder #%s to chat %s", reminder.id, chat_id)
        except Exception:
            logger.exception("Unexpected error delivering reminder #%s", reminder.id)
        finally:
            # Always advance/deactivate, even if delivery failed, so a single
            # broken chat can't spam retries forever or block other reminders.
            await advance_or_deactivate_reminder(reminder)
