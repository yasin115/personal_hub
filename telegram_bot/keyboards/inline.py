"""
Inline ("glass" / شیشه‌ای) keyboard builders.

Callback data convention: "<domain>:<action>:<arg>"
e.g. "hb:log:14", "td:done:3", "pg:habits:1" (pagination), "cf:yes:hb:del:14"

Keep callback_data short (<64 bytes) -- ids are fine, never embed free text.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ------------------------------------------------------------------
# Generic building blocks
# ------------------------------------------------------------------

def pagination_row(prefix: str, page: int, has_prev: bool, has_next: bool) -> list[InlineKeyboardButton]:
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"pg:{prefix}:{page - 1}"))
    row.append(InlineKeyboardButton(text=f"صفحه {page + 1}", callback_data="noop"))
    if has_next:
        row.append(InlineKeyboardButton(text="بعدی ➡️", callback_data=f"pg:{prefix}:{page + 1}"))
    return row


def confirm_kb(yes_cb: str, no_cb: str = "cf:cancel") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ بله، مطمئنم", callback_data=yes_cb)
    kb.button(text="❌ انصراف", callback_data=no_cb)
    kb.adjust(2)
    return kb.as_markup()


def back_to_menu_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="nav:home")]


# ------------------------------------------------------------------
# Linking
# ------------------------------------------------------------------

def link_account_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 دریافت کد اتصال حساب", callback_data="link:new")
    kb.adjust(1)
    return kb.as_markup()


# ------------------------------------------------------------------
# Habits
# ------------------------------------------------------------------

def habits_list_kb(habits, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for h in habits:
        icon = h.icon or "•"
        state = "⏸" if not h.is_active else "✅"
        kb.row(InlineKeyboardButton(text=f"{icon} {h.name}", callback_data=f"hb:view:{h.id}"))
        kb.row(
            InlineKeyboardButton(text="✅ ثبت امروز", callback_data=f"hb:log:{h.id}"),
            InlineKeyboardButton(text="📊 آمار", callback_data=f"hb:stats:{h.id}"),
            InlineKeyboardButton(text=f"{state} فعال/غیرفعال", callback_data=f"hb:toggle:{h.id}"),
        )
        kb.row(InlineKeyboardButton(text="🗑 حذف", callback_data=f"hb:delask:{h.id}"))
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("habits", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ افزودن عادت جدید", callback_data="hb:add"))
    return kb.as_markup()


def habit_frequency_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 روزانه", callback_data="hb:freq:daily")
    kb.button(text="🗓 هفتگی", callback_data="hb:freq:weekly")
    kb.button(text="🔧 سفارشی", callback_data="hb:freq:custom")
    kb.adjust(3)
    return kb.as_markup()


def skip_kb(skip_cb: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="↪️ رد کردن", callback_data=skip_cb)
    return kb.as_markup()


# ------------------------------------------------------------------
# Todos
# ------------------------------------------------------------------

def todos_list_kb(todos, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in todos:
        kb.row(InlineKeyboardButton(text=f"📌 {t.title}", callback_data=f"td:view:{t.id}"))
        kb.row(
            InlineKeyboardButton(text="✅ تکمیل شد", callback_data=f"td:done:{t.id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"td:delask:{t.id}"),
        )
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("todos", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ افزودن کار جدید", callback_data="td:add"))
    return kb.as_markup()


def todo_priority_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🟢 پایین", callback_data="td:pri:low")
    kb.button(text="🟡 متوسط", callback_data="td:pri:medium")
    kb.button(text="🟠 بالا", callback_data="td:pri:high")
    kb.button(text="🔴 فوری", callback_data="td:pri:urgent")
    kb.adjust(2)
    return kb.as_markup()


def todo_due_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 امروز", callback_data="td:due:today")
    kb.button(text="📆 فردا", callback_data="td:due:tomorrow")
    kb.button(text="🚫 بدون سررسید", callback_data="td:due:none")
    kb.adjust(2, 1)
    return kb.as_markup()


# ------------------------------------------------------------------
# Finance
# ------------------------------------------------------------------

def finance_home_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ ثبت تراکنش جدید", callback_data="fin:add")
    kb.button(text="📜 تراکنش‌های اخیر", callback_data="fin:recent:0")
    kb.adjust(1)
    return kb.as_markup()


def transactions_list_kb(items, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for tx in items:
        sign = "+" if tx.type == "income" else "-"
        label = f"{sign}{tx.amount:,.0f} {tx.currency} | {tx.date}"
        kb.row(InlineKeyboardButton(text=label, callback_data=f"fin:view:{tx.id}"))
        kb.row(InlineKeyboardButton(text="🗑 حذف این تراکنش", callback_data=f"fin:delask:{tx.id}"))
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("fin_recent", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ ثبت تراکنش جدید", callback_data="fin:add"))
    return kb.as_markup()


def tx_type_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 درآمد", callback_data="fin:type:income")
    kb.button(text="💸 هزینه", callback_data="fin:type:expense")
    kb.adjust(2)
    return kb.as_markup()


def category_kb(categories) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in categories:
        icon = c.icon or "🏷"
        kb.button(text=f"{icon} {c.name}", callback_data=f"fin:cat:{c.id}")
    kb.button(text="🚫 بدون دسته‌بندی", callback_data="fin:cat:none")
    kb.adjust(2)
    return kb.as_markup()


def tx_date_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 امروز", callback_data="fin:date:today")
    kb.button(text="📆 دیروز", callback_data="fin:date:yesterday")
    kb.adjust(2)
    return kb.as_markup()


# ------------------------------------------------------------------
# Reminders
# ------------------------------------------------------------------

def reminders_list_kb(items, page, total, per_page=5) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for r in items:
        kb.row(InlineKeyboardButton(text=f"🔔 {r.title}", callback_data=f"rm:view:{r.id}"))
        kb.row(
            InlineKeyboardButton(text="⏸ غیرفعال/فعال", callback_data=f"rm:toggle:{r.id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"rm:delask:{r.id}"),
        )
    has_prev = page > 0
    has_next = (page + 1) * per_page < total
    if has_prev or has_next:
        kb.row(*pagination_row("reminders", page, has_prev, has_next))
    kb.row(InlineKeyboardButton(text="➕ یادآور جدید", callback_data="rm:add"))
    return kb.as_markup()


def reminder_quick_time_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏰ ۱ ساعت دیگر", callback_data="rm:when:1h")
    kb.button(text="🌆 امروز عصر (۱۸:۰۰)", callback_data="rm:when:tonight")
    kb.button(text="🌅 فردا صبح (۹:۰۰)", callback_data="rm:when:tomorrow_morning")
    kb.button(text="✏️ وارد کردن دستی", callback_data="rm:when:manual")
    kb.adjust(1)
    return kb.as_markup()


def reminder_recurrence_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚫 بدون تکرار", callback_data="rm:rec:none")
    kb.button(text="📅 روزانه", callback_data="rm:rec:daily")
    kb.button(text="🗓 هفتگی", callback_data="rm:rec:weekly")
    kb.button(text="📆 ماهانه", callback_data="rm:rec:monthly")
    kb.adjust(2)
    return kb.as_markup()


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------

def settings_kb(is_linked: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_linked:
        kb.button(text="🔓 قطع اتصال حساب", callback_data="link:unlink:ask")
    else:
        kb.button(text="🔗 اتصال حساب", callback_data="link:new")
    kb.adjust(1)
    return kb.as_markup()
