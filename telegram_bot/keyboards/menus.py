"""Persistent reply (menu) keyboard -- always visible under the message box."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

BTN_HABITS = "📋 عادت‌ها"
BTN_TODOS = "✅ کارها"
BTN_FINANCE = "💰 مالی"
BTN_REMINDERS = "🔔 یادآورها"
BTN_SETTINGS = "⚙️ تنظیمات"
BTN_HELP = "❓ راهنما"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_HABITS), KeyboardButton(text=BTN_TODOS)],
            [KeyboardButton(text=BTN_FINANCE), KeyboardButton(text=BTN_REMINDERS)],
            [KeyboardButton(text=BTN_SETTINGS), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="یک گزینه را انتخاب کنید یا دستور بزنید...",
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
