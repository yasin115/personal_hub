"""
Account linking flow.

/start (when not linked) or /link shows a button -> bot generates a one-time
6-digit code (TelegramLinkCode, valid 10 minutes) tied to this chat_id.
The user enters that code on the website/app while logged in, which calls
POST /api/telegram/verify-link/ (see telegram_bot/views.py) to finish linking.

Unlinking is available from ⚙️ تنظیمات.
"""
from asgiref.sync import sync_to_async
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..models import TelegramLinkCode
from ..keyboards.inline import link_account_kb, confirm_kb, settings_kb
from ..utils import unlink_chat

router = Router(name="linking")


@sync_to_async
def _create_code(chat_id, username, first_name):
    return TelegramLinkCode.create_for_chat(chat_id, username or "", first_name or "")


def _code_text(code: TelegramLinkCode) -> str:
    return (
        "🔐 <b>کد اتصال حساب شما:</b>\n\n"
        f"<code>{code.code}</code>\n\n"
        "این کد را در وبسایت یا اپ Personal Hub، در بخش «پروفایل ← اتصال تلگرام» وارد کنید.\n"
        "⏳ اعتبار: ۱۰ دقیقه\n\n"
        "اگر کد منقضی شد، دوباره دستور /link را بزنید یا دکمه زیر را لمس کنید."
    )


@router.message(Command("link"))
async def cmd_link(message: Message, django_user):
    if django_user:
        return await message.answer("✅ حساب شما همین الان هم متصل است.")
    code = await _create_code(message.chat.id, message.from_user.username, message.from_user.first_name)
    await message.answer(_code_text(code), reply_markup=link_account_kb())


@router.callback_query(F.data == "link:new")
async def cb_link_new(callback: CallbackQuery, django_user):
    if django_user:
        await callback.answer("✅ حساب شما همین الان هم متصل است.", show_alert=True)
        return
    code = await _create_code(
        callback.message.chat.id, callback.from_user.username, callback.from_user.first_name
    )
    await callback.message.answer(_code_text(code), reply_markup=link_account_kb())
    await callback.answer()


@router.callback_query(F.data == "link:unlink:ask")
async def cb_unlink_ask(callback: CallbackQuery, django_user):
    if not django_user:
        return await callback.answer()
    await callback.message.answer(
        "⚠️ مطمئن هستید می‌خواهید اتصال حساب تلگرام را قطع کنید؟\n"
        "بعد از قطع اتصال، دیگر نمی‌توانید از این ربات برای این حساب استفاده کنید مگر دوباره وصل کنید.",
        reply_markup=confirm_kb(yes_cb="link:unlink:yes"),
    )
    await callback.answer()


@router.callback_query(F.data == "link:unlink:yes")
async def cb_unlink_yes(callback: CallbackQuery):
    await unlink_chat(callback.message.chat.id)
    await callback.message.edit_text("🔓 اتصال حساب قطع شد.")
    await callback.message.answer("برای اتصال مجدد:", reply_markup=link_account_kb())
    await callback.answer()
