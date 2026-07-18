"""
Common handlers: /start, /help, /cancel, /menu, the main reply-keyboard
buttons, settings, and the final "unknown message" fallback.
"""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..keyboards.menus import (
    main_menu_kb, BTN_HABITS, BTN_TODOS, BTN_FINANCE, BTN_REMINDERS, BTN_SETTINGS, BTN_HELP,
)
from ..keyboards.inline import link_account_kb, settings_kb
from ..utils import esc

router = Router(name="common")


HELP_TEXT = (
    "📌 <b>راهنمای ربات Personal Hub</b>\n\n"
    "از منوی پایین صفحه یا دستورات زیر استفاده کنید:\n\n"
    "📋 <b>عادت‌ها</b>\n"
    "/habits — لیست و مدیریت عادات\n\n"
    "✅ <b>کارها</b>\n"
    "/todos — لیست و مدیریت کارها\n\n"
    "💰 <b>مالی</b>\n"
    "/balance — خلاصه مالی و ثبت تراکنش\n\n"
    "🔔 <b>یادآورها</b>\n"
    "/reminders — لیست و مدیریت یادآورها\n\n"
    "⚙️ /settings — تنظیمات و اتصال حساب\n"
    "❌ /cancel — لغو عملیات جاری (فرم‌های چند مرحله‌ای)\n"
    "🏠 /menu — نمایش منوی اصلی"
)


@router.message(CommandStart())
async def cmd_start(message: Message, django_user, state: FSMContext):
    await state.clear()
    if django_user:
        name = esc(django_user.first_name or django_user.username)
        await message.answer(
            f"سلام {name}! 👋\n\nبه <b>Personal Hub</b> خوش آمدید.\n"
            "از منوی پایین صفحه بخش مورد نظر را انتخاب کنید 👇",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(
            "سلام! 👋\n\n"
            "این ربات به حساب Personal Hub شما وصل می‌شود تا بتوانید عادت‌ها، "
            "کارها، تراکنش‌های مالی و یادآورهایتان را همینجا هم مدیریت کنید.\n\n"
            "برای شروع، حساب‌تان را وصل کنید:",
            reply_markup=link_account_kb(),
        )


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)


@router.message(Command("menu"))
async def cmd_menu(message: Message, django_user):
    if not django_user:
        return await message.answer(
            "ابتدا حساب‌تان را وصل کنید:", reply_markup=link_account_kb()
        )
    await message.answer("🏠 منوی اصلی:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "nav:home")
async def cb_nav_home(callback: CallbackQuery):
    await callback.message.answer("🏠 منوی اصلی:", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        return await message.answer("چیزی برای لغو کردن وجود ندارد.")
    await state.clear()
    await message.answer("❌ عملیات لغو شد.", reply_markup=main_menu_kb())


@router.message(Command("settings"))
@router.message(F.text == BTN_SETTINGS)
async def cmd_settings(message: Message, django_user):
    if not django_user:
        return await message.answer(
            "حساب شما وصل نیست.", reply_markup=link_account_kb()
        )
    text = (
        f"⚙️ <b>تنظیمات</b>\n\n"
        f"👤 کاربر: {esc(django_user.username)}\n"
        f"🔗 وضعیت اتصال: متصل ✅"
    )
    await message.answer(text, reply_markup=settings_kb(is_linked=True))


@router.callback_query(F.data == "cf:cancel")
async def cb_generic_cancel(callback: CallbackQuery):
    await callback.answer("لغو شد.")
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


# NOTE: keep this fallback registered LAST (see handlers/__init__.py ordering)
# so it only catches messages no other router matched (typos, chit-chat, etc.)
@router.message(F.text)
async def unknown_message(message: Message, django_user):
    if django_user:
        await message.answer(
            "متوجه این پیام نشدم 🤔 از منوی پایین صفحه استفاده کنید یا /help را بزنید.",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(
            "متوجه این پیام نشدم 🤔 برای شروع، /start را بزنید.",
        )
