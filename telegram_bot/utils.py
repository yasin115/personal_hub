"""
Shared helpers for the Telegram bot: async ORM access, formatting, small parsers.
Keeping all Django-ORM access here (wrapped in sync_to_async) means handler files
stay thin and readable, and it's the single place to extend if the schema changes.
"""
from __future__ import annotations

import re
import html
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from asgiref.sync import sync_to_async
from django.utils import timezone

from accounts.models import Profile
from habits.models import Habit, HabitLog
from todos.models import Todo
from finance.models import Transaction, TransactionCategory
from reminders.models import Reminder


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def esc(text) -> str:
    """Escape user-generated text before putting it in an HTML-parsed message."""
    if text is None:
        return ""
    return html.escape(str(text), quote=False)


def fmt_money(amount: Decimal | int | float, currency: str = "IRR") -> str:
    try:
        return f"{Decimal(amount):,.0f} {currency}"
    except (InvalidOperation, TypeError):
        return f"{amount} {currency}"


def fmt_dt(dt: datetime) -> str:
    local = timezone.localtime(dt) if timezone.is_aware(dt) else dt
    return local.strftime("%Y-%m-%d %H:%M")


PRIORITY_LABEL = {"low": "🟢 پایین", "medium": "🟡 متوسط", "high": "🟠 بالا", "urgent": "🔴 فوری"}
STATUS_LABEL = {
    "pending": "⏳ در انتظار",
    "in_progress": "🔄 در حال انجام",
    "completed": "✅ انجام شده",
    "cancelled": "🚫 لغو شده",
}
FREQUENCY_LABEL = {"daily": "روزانه", "weekly": "هفتگی", "custom": "سفارشی"}
RECURRENCE_LABEL = {
    "none": "بدون تکرار", "daily": "روزانه", "weekly": "هفتگی",
    "monthly": "ماهانه", "custom": "سفارشی",
}
TX_TYPE_LABEL = {"income": "درآمد 💵", "expense": "هزینه 💸"}


# ------------------------------------------------------------------
# Natural-ish date/time parsing for FSM text input
# ------------------------------------------------------------------

WEEKDAY_NONE = object()


def parse_simple_date(text: str) -> date | None:
    """Accepts: امروز / دیروز / فردا / YYYY-MM-DD"""
    text = text.strip()
    today = date.today()
    mapping = {
        "امروز": today,
        "دیروز": today - timedelta(days=1),
        "فردا": today + timedelta(days=1),
    }
    if text in mapping:
        return mapping[text]
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def parse_simple_datetime(text: str) -> datetime | None:
    """Accepts: 'YYYY-MM-DD HH:MM' or 'HH:MM' (today) or 'فردا HH:MM'."""
    text = text.strip()
    now = timezone.localtime(timezone.now())

    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$", text)
    if m:
        y, mo, d, h, mi = map(int, m.groups())
        try:
            naive = datetime(y, mo, d, h, mi)
            return timezone.make_aware(naive)
        except ValueError:
            return None

    m = re.match(r"^فردا\s+(\d{1,2}):(\d{2})$", text)
    if m:
        h, mi = map(int, m.groups())
        target = (now + timedelta(days=1)).replace(hour=h, minute=mi, second=0, microsecond=0)
        return target

    m = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if m:
        h, mi = map(int, m.groups())
        target = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    return None


def parse_amount(text: str) -> Decimal | None:
    cleaned = text.strip().replace(",", "").replace("،", "")
    # Convert Persian/Arabic digits to ASCII
    digit_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    cleaned = cleaned.translate(digit_map)
    try:
        value = Decimal(cleaned)
        if value <= 0:
            return None
        return value
    except InvalidOperation:
        return None


# ------------------------------------------------------------------
# ORM access (sync -> async bridges)
# ------------------------------------------------------------------

@sync_to_async
def get_user_from_chat_id(chat_id: int):
    try:
        return Profile.objects.select_related("user").get(telegram_chat_id=chat_id).user
    except Profile.DoesNotExist:
        return None


@sync_to_async
def unlink_chat(chat_id: int):
    updated = Profile.objects.filter(telegram_chat_id=chat_id).update(telegram_chat_id=None)
    return bool(updated)


# ---- Habits ----

@sync_to_async
def list_habits(user, active_only=True, offset=0, limit=5):
    qs = Habit.objects.filter(user=user)
    if active_only:
        qs = qs.filter(is_active=True)
    total = qs.count()
    items = list(qs.order_by("-created_at")[offset:offset + limit])
    return items, total


@sync_to_async
def get_habit(user, habit_id):
    return Habit.objects.filter(user=user, id=habit_id).first()


@sync_to_async
def create_habit(user, name, frequency, icon):
    return Habit.objects.create(user=user, name=name, frequency=frequency, icon=icon or "")


@sync_to_async
def toggle_habit_active(user, habit_id):
    habit = Habit.objects.filter(user=user, id=habit_id).first()
    if habit:
        habit.is_active = not habit.is_active
        habit.save(update_fields=["is_active"])
    return habit


@sync_to_async
def delete_habit(user, habit_id):
    return Habit.objects.filter(user=user, id=habit_id).delete()


@sync_to_async
def log_habit_today(habit, user):
    today = date.today()
    log, created = HabitLog.objects.get_or_create(
        habit=habit, date=today, defaults={"user": user, "completed": True, "count": 1}
    )
    if not created:
        log.completed = True
        log.count = (log.count or 0) + 1
        log.save(update_fields=["completed", "count"])
    return log, created


@sync_to_async
def habit_stats(habit, days=30):
    since = date.today() - timedelta(days=days)
    logs = habit.logs.filter(date__gte=since, completed=True)
    return logs.count()


# ---- Todos ----

@sync_to_async
def list_todos(user, statuses=("pending", "in_progress"), offset=0, limit=5):
    qs = Todo.objects.filter(user=user, status__in=statuses, parent__isnull=True)
    total = qs.count()
    items = list(qs.order_by("order", "-created_at")[offset:offset + limit])
    return items, total


@sync_to_async
def get_todo(user, todo_id):
    return Todo.objects.filter(user=user, id=todo_id).first()


@sync_to_async
def create_todo(user, title, priority="medium", due_date=None):
    return Todo.objects.create(user=user, title=title, priority=priority, due_date=due_date)


@sync_to_async
def complete_todo(user, todo_id):
    todo = Todo.objects.filter(user=user, id=todo_id).first()
    if todo:
        todo.mark_completed()
    return todo


@sync_to_async
def delete_todo(user, todo_id):
    return Todo.objects.filter(user=user, id=todo_id).delete()


# ---- Finance ----

@sync_to_async
def get_finance_totals(user):
    from django.db.models import Sum
    income = Transaction.objects.filter(user=user, type="income").aggregate(total=Sum("amount"))["total"] or Decimal(0)
    expense = Transaction.objects.filter(user=user, type="expense").aggregate(total=Sum("amount"))["total"] or Decimal(0)
    return income, expense


@sync_to_async
def list_categories(user, tx_type):
    return list(
        TransactionCategory.objects.filter(models_q_user_or_default(user)).filter(
            **({} if tx_type is None else {"type__in": [tx_type, "both"]})
        )[:20]
    )


def models_q_user_or_default(user):
    from django.db.models import Q
    return Q(user=user) | Q(is_default=True)


@sync_to_async
def get_category(user, category_id):
    return TransactionCategory.objects.filter(id=category_id).filter(models_q_user_or_default(user)).first()


@sync_to_async
def create_transaction(user, tx_type, amount, category, tx_date, description=""):
    return Transaction.objects.create(
        user=user, type=tx_type, amount=amount, category=category,
        date=tx_date, description=description,
    )


@sync_to_async
def list_recent_transactions(user, offset=0, limit=5):
    qs = Transaction.objects.filter(user=user).select_related("category")
    total = qs.count()
    items = list(qs.order_by("-date", "-created_at")[offset:offset + limit])
    return items, total


@sync_to_async
def get_transaction(user, tx_id):
    return Transaction.objects.filter(user=user, id=tx_id).first()


@sync_to_async
def delete_transaction(user, tx_id):
    return Transaction.objects.filter(user=user, id=tx_id).delete()


# ---- Reminders ----

@sync_to_async
def list_reminders(user, upcoming_only=True, offset=0, limit=5):
    qs = Reminder.objects.filter(user=user, is_active=True)
    if upcoming_only:
        qs = qs.filter(remind_at__gte=timezone.now())
    total = qs.count()
    items = list(qs.order_by("remind_at")[offset:offset + limit])
    return items, total


@sync_to_async
def get_reminder(user, reminder_id):
    return Reminder.objects.filter(user=user, id=reminder_id).first()


@sync_to_async
def create_reminder(user, title, remind_at, recurrence_type="none"):
    return Reminder.objects.create(
        user=user, title=title, remind_at=remind_at,
        is_recurring=recurrence_type != "none", recurrence_type=recurrence_type,
    )


@sync_to_async
def toggle_reminder_active(user, reminder_id):
    r = Reminder.objects.filter(user=user, id=reminder_id).first()
    if r:
        r.is_active = not r.is_active
        r.save(update_fields=["is_active"])
    return r


@sync_to_async
def delete_reminder(user, reminder_id):
    return Reminder.objects.filter(user=user, id=reminder_id).delete()
