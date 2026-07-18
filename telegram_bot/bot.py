"""
Personal Hub Telegram Bot -- aiogram 3.x

Run with:
    python manage.py runbot

Architecture (each piece is easy to find & extend):
    models.py            -> TelegramLinkCode (account-linking codes)
    states.py            -> FSM StatesGroup definitions for multi-step add wizards
    middlewares.py       -> DjangoUserMiddleware resolves the linked user for every update
    utils.py             -> all Django ORM access (async-wrapped) + formatting/parsing helpers
    scheduler.py         -> background loop that actually fires reminders on time
    keyboards/menus.py   -> the persistent bottom reply-keyboard (main menu)
    keyboards/inline.py  -> all inline ("glass") keyboards: lists, wizards, confirmations
    handlers/            -> one Router per feature area (common, linking, habits, todos,
                             finance, reminders) -- see handlers/__init__.py for how
                             they're wired together and how to add a new one.

To add a whole new feature (say "notes"):
    1. Add ORM helpers to utils.py.
    2. Add keyboards to keyboards/inline.py.
    3. Create handlers/notes.py with its own Router (copy habits.py as a template).
    4. Register it in handlers/__init__.py's `all_routers` list.
Nothing else here needs to change.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_hub.settings")
django.setup()

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from django.conf import settings

from telegram_bot.middlewares import DjangoUserMiddleware
from telegram_bot.handlers import all_routers
from telegram_bot.scheduler import reminder_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("telegram_bot")

from pathlib import Path

async def notify_admin_of_pending_deploy(bot: Bot):
    admin_id = getattr(settings, "ADMIN_TELEGRAM_ID", None)
    result_file = Path(settings.BASE_DIR) / "run" / "deploy_result"
    if not admin_id or not result_file.exists():
        return
    try:
        result = result_file.read_text().strip()
        result_file.unlink(missing_ok=True)
        if result.startswith("UPDATED"):
            await bot.send_message(admin_id, "✅ آپدیت با موفقیت اعمال شد و ربات دوباره بالا اومد.")
    except Exception:
        logger.exception("Failed to send deploy-result notification")

async def main():
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: TELEGRAM_BOT_TOKEN را در settings.py یا متغیر محیطی تنظیم کنید!")
        return

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await notify_admin_of_pending_deploy(bot)
    # MemoryStorage is fine for a single-process polling bot. If you scale to
    # multiple workers or use webhooks, swap this for RedisStorage so FSM
    # state (the multi-step "add" wizards) survives restarts / is shared.
    dp = Dispatcher(storage=MemoryStorage())

    django_user_middleware = DjangoUserMiddleware()
    dp.message.outer_middleware(django_user_middleware)
    dp.callback_query.outer_middleware(django_user_middleware)

    for router in all_routers:
        dp.include_router(router)

    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        """
        Catch-all so one bad update (bad input, a race on a deleted row, a
        transient Telegram API hiccup, ...) never takes the whole bot down --
        it just logs and replies with a friendly message instead of hanging
        or crashing the polling loop.
        """
        logger.exception("Unhandled error while processing update", exc_info=event.exception)
        update = event.update
        try:
            if update.callback_query:
                await update.callback_query.answer("⚠️ مشکلی پیش اومد. دوباره امتحان کنید.", show_alert=True)
            elif update.message:
                await update.message.answer("⚠️ مشکلی پیش اومد. لطفاً دوباره امتحان کنید یا /start را بزنید.")
        except Exception:
            pass
        return True

    print("🤖 Personal Hub Telegram Bot (aiogram 3) در حال اجرا است...")
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler_task = asyncio.create_task(reminder_loop(bot))
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        scheduler_task.cancel()


def run_bot():
    """Entry point for the `runbot` Django management command."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nربات متوقف شد.")


if __name__ == "__main__":
    run_bot()
