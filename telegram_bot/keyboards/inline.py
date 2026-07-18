"""
Inline ("glass" / شیشه‌ای) keyboard builders.

Update: Telegram Bot API 9.4 (2026-02-09) added a real per-button `style`
field -- 'success' (green), 'danger' (red), 'primary' (blue) -- exposed by
aiogram as `InlineKeyboardButton(..., style=...)` / `builder.button(...,
style=...)` since aiogram 3.25/3.26. This file uses that everywhere it makes
sense (requires aiogram>=3.26 -- see the note in telegram_bot/README.md).
Color-emoji prefixes are kept alongside `style` for section grouping
per domain) and for older clients/themes that may not render the
native style yet.

Callback data convention: "<domain>:<action>:<arg>"
e.g. "hb:log:14", "td:done:3", "pg:habits:1" (pagination)
Keep callback_data short (<64 bytes) -- ids are fine, never embed free text.
"""
import os

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

SUCCESS = "success"
DANGER = "danger"
PRIMARY = "primary"

# If set (e.g. `export MINI_APP_URL=https://yourdomain.com/`), the "connect
# account" button opens the Telegram Mini App directly -- the smoothest
# possible flow: tap once, log in/register or land already-logged-in, and
# the account links itself automatically (see webapp/static/webapp/app.js
# and telegram_bot/webapp_auth.py). Must be a real https:// URL -- Telegram
# rejects http:// and self-signed certs for Web Apps. Without it, the bot
# falls back to the deep-link + manual-code flow (still zero-typing on
# mobile, just one extra hop through the browser instead of staying
# natively inside Telegram).
MINI_APP_URL = os.environ.get("MINI_APP_URL", "").strip()


# ------------------------------------------------------------------
# Generic building blocks
# ------------------------------------------------------------------

def pagination_row(prefix: str, page: int, has_prev: bool, has_next: bool) -> list[InlineKeyboardButton]:
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"pg:{prefix}:{page - 1}", style=PRIMARY))
    row.append(InlineKeyboardButton(text=f"📄 {page + 1}", callback_data="noop"))
    if has_next:
        row.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"pg:{prefix}:{page + 1}", style=PRIMARY))
    return row


def confirm_kb(yes_cb: str, no_cb: str = "cf:cancel") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ بله، مطمئنم", callback_data=yes_cb, style=SUCCESS)
    kb.button(text="❌ انصراف", callback_data=no_cb, style=DANGER)
    kb.adjust(2)
    return kb.as_markup()


def back_to_menu_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="nav:home", style=PRIMARY)]


# ------------------------------------------------------------------
# Linking
# ------------------------------------------------------------------

def link_account_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if MINI_APP_URL:
        kb.button(text="🔗 اتصال حساب", web_app=WebAppInfo(url=MINI_APP_URL))
    else:
        kb.button(text="🔗 دریافت کد اتصال حساب", callback_data="link:new", style=SUCCESS)
    kb.adjust(1)
    return kb.as_markup()


# ------------------------------------------------------------------
# Habits 📋
# ------------------------------------------------------------------

def habits_list_kb(habits, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for h in habits:
        icon = h.icon or "📌"
        state_dot = "🟢" if h.is_active else "⚪️"
        kb.row(InlineKeyboardButton(
            text=f"{icon} {h.name} {state_dot}", callback_data=f"hb:view:{h.id}", style=PRIMARY
        ))
        kb.row(
            InlineKeyboardButton(text="✅ ثبت امروز", callback_data=f"hb:log:{h.id}", style=SUCCESS),
            InlineKeyboardButton(text="📊 آمار", callback_data=f"hb:stats:{h.id}", style=PRIMARY),
        )
        kb.row(
            InlineKeyboardButton(text="⏯ فعال/غیرفعال", callback_data=f"hb:toggle:{h.id}", style=PRIMARY),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"hb:delask:{h.id}", style=DANGER),
        )
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("habits", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ افزودن عادت جدید", callback_data="hb:add", style=SUCCESS))
    kb.row(*back_to_menu_row())
    return kb.as_markup()


def habit_frequency_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 روزانه", callback_data="hb:freq:daily", style=PRIMARY)
    kb.button(text="🗓 هفتگی", callback_data="hb:freq:weekly", style=PRIMARY)
    kb.button(text="🔧 سفارشی", callback_data="hb:freq:custom", style=PRIMARY)
    kb.adjust(3)
    return kb.as_markup()


def skip_kb(skip_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="↪️ رد کردن", callback_data=skip_cb)
    return kb.as_markup()


# ------------------------------------------------------------------
# Todos ✅
# ------------------------------------------------------------------

_PRIORITY_DOT = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}


def todos_list_kb(todos, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in todos:
        dot = _PRIORITY_DOT.get(t.priority, "⚪️")
        due = f" 📅{t.due_date.strftime('%m-%d')}" if t.due_date else ""
        kb.row(InlineKeyboardButton(
            text=f"{dot} {t.title}{due}", callback_data=f"td:view:{t.id}", style=PRIMARY
        ))
        kb.row(
            InlineKeyboardButton(text="✅ تکمیل شد", callback_data=f"td:done:{t.id}", style=SUCCESS),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"td:delask:{t.id}", style=DANGER),
        )
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("todos", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ افزودن کار جدید", callback_data="td:add", style=SUCCESS))
    kb.row(*back_to_menu_row())
    return kb.as_markup()


def todo_priority_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🟢 پایین", callback_data="td:pri:low", style=SUCCESS)
    kb.button(text="🟡 متوسط", callback_data="td:pri:medium", style=PRIMARY)
    kb.button(text="🟠 بالا", callback_data="td:pri:high", style=PRIMARY)
    kb.button(text="🔴 فوری", callback_data="td:pri:urgent", style=DANGER)
    kb.adjust(2)
    return kb.as_markup()


def todo_due_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 امروز", callback_data="td:due:today", style=PRIMARY)
    kb.button(text="📆 فردا", callback_data="td:due:tomorrow", style=PRIMARY)
    kb.button(text="🚫 بدون سررسید", callback_data="td:due:none", style=DANGER)
    kb.adjust(2, 1)
    return kb.as_markup()


# ------------------------------------------------------------------
# Finance 💰
# ------------------------------------------------------------------

def finance_home_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ ثبت تراکنش جدید", callback_data="fin:add", style=SUCCESS)
    kb.button(text="📜 تراکنش‌های اخیر", callback_data="fin:recent:0", style=PRIMARY)
    kb.adjust(1)
    kb.row(*back_to_menu_row())
    return kb.as_markup()


def transactions_list_kb(items, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for tx in items:
        sign = "+" if tx.type == "income" else "-"
        label = f"{sign}{tx.amount:,.0f} {tx.currency} · {tx.date}"
        row_style = SUCCESS if tx.type == "income" else DANGER
        kb.row(InlineKeyboardButton(text=label, callback_data=f"fin:view:{tx.id}", style=row_style))
        kb.row(InlineKeyboardButton(text="🗑 حذف این تراکنش", callback_data=f"fin:delask:{tx.id}", style=DANGER))
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("fin_recent", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ ثبت تراکنش جدید", callback_data="fin:add", style=SUCCESS))
    kb.row(*back_to_menu_row())
    return kb.as_markup()


def tx_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 درآمد", callback_data="fin:type:income", style=SUCCESS)
    kb.button(text="💸 هزینه", callback_data="fin:type:expense", style=DANGER)
    kb.adjust(2)
    return kb.as_markup()


def category_kb(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in categories:
        icon = c.icon or "🏷"
        kb.button(text=f"{icon} {c.name}", callback_data=f"fin:cat:{c.id}", style=PRIMARY)
    kb.button(text="⚪️ بدون دسته‌بندی", callback_data="fin:cat:none")
    kb.adjust(2)
    return kb.as_markup()


def tx_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 امروز", callback_data="fin:date:today", style=PRIMARY)
    kb.button(text="📆 دیروز", callback_data="fin:date:yesterday", style=PRIMARY)
    kb.adjust(2)
    return kb.as_markup()


# ------------------------------------------------------------------
# Reminders ⏰
# ------------------------------------------------------------------

def reminders_list_kb(items, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in items:
        dot = "🟢" if r.is_active else "⚪️"
        kb.row(InlineKeyboardButton(
            text=f"🔔 {r.title} {dot}", callback_data=f"rm:view:{r.id}", style=PRIMARY
        ))
        kb.row(
            InlineKeyboardButton(text="⏯ فعال/غیرفعال", callback_data=f"rm:toggle:{r.id}", style=PRIMARY),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"rm:delask:{r.id}", style=DANGER),
        )
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("reminders", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ یادآور جدید", callback_data="rm:add", style=SUCCESS))
    kb.row(*back_to_menu_row())
    return kb.as_markup()


def reminder_quick_time_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏰ ۱ ساعت دیگر", callback_data="rm:when:1h", style=PRIMARY)
    kb.button(text="🌆 امروز عصر (۱۸:۰۰)", callback_data="rm:when:tonight", style=PRIMARY)
    kb.button(text="🌅 فردا صبح (۹:۰۰)", callback_data="rm:when:tomorrow_morning", style=PRIMARY)
    kb.button(text="✏️ وارد کردن دستی", callback_data="rm:when:manual")
    kb.adjust(1)
    return kb.as_markup()


def reminder_recurrence_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚫 بدون تکرار", callback_data="rm:rec:none", style=DANGER)
    kb.button(text="📅 روزانه", callback_data="rm:rec:daily", style=PRIMARY)
    kb.button(text="🗓 هفتگی", callback_data="rm:rec:weekly", style=PRIMARY)
    kb.button(text="📆 ماهانه", callback_data="rm:rec:monthly", style=PRIMARY)
    kb.adjust(2)
    return kb.as_markup()


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------

def settings_kb(is_linked: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_linked:
        kb.button(text="🔓 قطع اتصال حساب", callback_data="link:unlink:ask", style=DANGER)
    elif MINI_APP_URL:
        kb.button(text="🔗 اتصال حساب", web_app=WebAppInfo(url=MINI_APP_URL))
    else:
        kb.button(text="🔗 اتصال حساب", callback_data="link:new", style=SUCCESS)
    kb.adjust(1)
    kb.row(*back_to_menu_row())
    return kb.as_markup()
