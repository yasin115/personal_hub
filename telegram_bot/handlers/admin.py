"""
Admin-only handler: lets the bot admin (by numeric Telegram id, see
settings.ADMIN_TELEGRAM_ID) trigger a self-update straight from the chat by
sending "update" or "آپدیت".

Flow:
    1. Admin sends "update" / "آپدیت".
    2. We reply immediately, then launch scripts/deploy.sh as a fully
       detached background process (its own session -- NOT a child of this
       bot process, so it survives this process being killed).
    3. deploy.sh checks GitHub for new commits.
         - Nothing new: it exits fast, writes "NO_UPDATE" to
           run/deploy_result, and this bot process is never touched -- we
           poll for that file for a few seconds and reply directly.
         - New commits: it pulls them (replacing changed files, adding new
           ones), reinstalls requirements, migrates, kills the running
           runserver/runbot processes, and restarts both with nohup. That
           kill takes this very bot process down, so we can't reply with
           the final result from here.
    4. On the NEXT bot startup, bot.py checks run/deploy_result and messages
       the admin with the outcome -- see `notify_admin_of_pending_deploy()`
       in bot.py, which closes the loop.
"""
import asyncio
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message
from django.conf import settings

router = Router(name="admin")
logger = logging.getLogger("telegram_bot")

BASE_DIR = Path(settings.BASE_DIR)
DEPLOY_SCRIPT = BASE_DIR / "scripts" / "deploy.sh"
RESULT_FILE = BASE_DIR / "run" / "deploy_result"

UPDATE_TRIGGERS = {"update", "آپدیت"}


def _is_admin(user_id: int | None) -> bool:
    admin_id = getattr(settings, "ADMIN_TELEGRAM_ID", None)
    return user_id is not None and admin_id is not None and user_id == admin_id


@router.message(F.text.func(lambda t: bool(t) and t.strip().lower() in UPDATE_TRIGGERS))
async def cmd_update(message: Message):
    # Silently ignore for anyone but the admin -- don't reveal this exists.
    if not _is_admin(message.from_user.id if message.from_user else None):
        return

    if not DEPLOY_SCRIPT.exists():
        return await message.answer(f"❌ اسکریپت پیدا نشد: {DEPLOY_SCRIPT}")

    RESULT_FILE.parent.mkdir(exist_ok=True)
    RESULT_FILE.unlink(missing_ok=True)

    await message.answer("🔄 در حال بررسی آپدیت از گیت‌هاب...")

    try:
        await asyncio.create_subprocess_exec(
            "bash", str(DEPLOY_SCRIPT),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,  # fully detach: survives this process dying
        )
    except Exception as e:
        logger.exception("Failed to launch deploy.sh")
        return await message.answer(f"❌ اجرای اسکریپت آپدیت شکست خورد: {e}")

    # Poll briefly: if there's genuinely nothing to update, deploy.sh exits
    # fast and this process is never killed, so we can answer directly.
    for _ in range(15):
        await asyncio.sleep(1)
        if RESULT_FILE.exists():
            result = RESULT_FILE.read_text().strip()
            if result == "NO_UPDATE":
                return await message.answer("✅ ریپازیتوری از قبل به‌روزه. تغییری اعمال نشد.")
            if result.startswith("UPDATED"):
                # If we're still alive to send this, the restart is imminent.
                return await message.answer(
                    "⬇️ آپدیت پیدا شد. در حال اعمال تغییرات و ری‌استارت سرور و ربات..."
                )
            if result.startswith("ERROR"):
                return await message.answer(f"❌ خطا در آپدیت: {result}")
            return
    # No result file yet after 15s: deploy is likely still installing deps
    # or migrating, or this process has already been replaced. Either way,
    # the startup notice in bot.py will report the final outcome.
