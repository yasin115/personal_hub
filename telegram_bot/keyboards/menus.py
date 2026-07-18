"""
Persistent reply (menu) keyboard -- always visible under the message box.

Uses Telegram's native per-button `style` field (Bot API 9.4+, aiogram>=3.25)
for real color -- 'success' (green), 'danger' (red), 'primary' (blue) -- paired
with a meaningful icon per section instead of plain colored squares. These
constants are the one place that defines each button's label, so every
handler filtering on `F.text == BTN_...` stays in sync automatically.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

BTN_HABITS = "📋 عادت‌ها"
BTN_TODOS = "✅ کارها"
BTN_FINANCE = "💰 مالی"
BTN_REMINDERS = "⏰ یادآورها"
BTN_SETTINGS = "⚙️ تنظیمات"
BTN_HELP = "ℹ️ راهنما"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_HABITS, style="primary"),
                KeyboardButton(text=BTN_TODOS, style="success"),
            ],
            [
                KeyboardButton(text=BTN_FINANCE, style="primary"),
                KeyboardButton(text=BTN_REMINDERS, style="primary"),
            ],
            [
                KeyboardButton(text=BTN_SETTINGS),
                KeyboardButton(text=BTN_HELP),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="یک گزینه را انتخاب کنید یا دستور بزنید...",
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
