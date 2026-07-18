"""
Personal Hub Telegram Bot -- aiogram 3.x

Run with:
    python manage.py runbot

Architecture (each piece is easy to find & extend):
    models.py           -> TelegramLinkCode (account-linking codes)
    states.py           -> FSM StatesGroup definitions for multi-step add wizards
    middlewares.py       -> DjangoUserMiddleware resolves the linked user for every update
    utils.py             -> all Django ORM access (async-wrapped) + formatting/parsing helpers
    keyboards/menus.py   -> the persistent bottom reply-keyboard (main menu)
    keyboards/inline.py  -> all inline ("glass") keyboards: lists, wizards, confirmations
    handlers/            -> one Router per feature area (common, linking, habits, todos,
                             finance, reminders) -- see handlers/__init__.py for how
                             they're wired together and how to add a new one.

To add a whole new feature (say "notes"):
    1. habits/todos-style Django app already exists elsewhere for the data model.
    2. Add ORM helpers to utils.py.
    3. Add keyboards to keyboards/inline.py.
    4. Create handlers/notes.py with its own Router (copy habits.py as a template).
    5. Register it in handlers/__init__.py's `all_routers` list.
Nothing else here needs to change.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_hub.settings")
django.setup()

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings

from telegram_bot.middlewares import DjangoUserMiddleware
from telegram_bot.handlers import all_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")


async def main():
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: TELEGRAM_BOT_TOKEN را در settings.py یا متغیر محیطی تنظیم کنید!")
        return

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # MemoryStorage is fine for a single-process polling bot. If you scale to
    # multiple workers or use webhooks, swap this for RedisStorage so FSM
    # state (the multi-step "add" wizards) survives restarts / is shared.
    dp = Dispatcher(storage=MemoryStorage())

    django_user_middleware = DjangoUserMiddleware()
    dp.message.outer_middleware(django_user_middleware)
    dp.callback_query.outer_middleware(django_user_middleware)

    for router in all_routers:
        dp.include_router(router)

    print("🤖 Personal Hub Telegram Bot (aiogram 3) در حال اجرا است...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


def run_bot():
    """Entry point for the `runbot` Django management command."""
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nربات متوقف شد.")


if __name__ == "__main__":
    run_bot()
