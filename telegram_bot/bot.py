"""
Personal Hub Telegram Bot - rewritten with aiogram 3.x
Much more flexible, modern, and powerful than python-telegram-bot.

Run with:
    python manage.py runbot

Features:
- Account linking via telegram_chat_id (set in web/app profile)
- Quick habit logging, todo creation, finance summary, reminders
- Clean command structure + easy to extend with routers, middlewares, FSM, etc.
"""
import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "personal_hub.settings")
django.setup()

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode
from asgiref.sync import sync_to_async
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import Profile
from habits.models import Habit, HabitLog
from todos.models import Todo
from finance.models import Transaction
from reminders.models import Reminder


# ============================================
# HELPER FUNCTIONS (Django ORM in async context)
# ============================================

@sync_to_async
def get_user_from_chat_id(chat_id: int):
    """Get Django User from linked Telegram chat_id"""
    try:
        profile = Profile.objects.select_related("user").get(telegram_chat_id=chat_id)
        return profile.user
    except Profile.DoesNotExist:
        return None


@sync_to_async
def get_active_habits(user):
    return list(Habit.objects.filter(user=user, is_active=True)[:10])


@sync_to_async
def get_or_create_habit_log(habit, today, user):
    log, created = HabitLog.objects.get_or_create(
        habit=habit,
        date=today,
        defaults={"user": user, "completed": True, "count": 1}
    )
    if not created:
        log.completed = True
        log.count = (log.count or 0) + 1
        log.save()
    return log, created


@sync_to_async
def create_todo(user, title):
    return Todo.objects.create(user=user, title=title, status="pending")


@sync_to_async
def get_pending_todos(user):
    return list(Todo.objects.filter(user=user, status__in=["pending", "in_progress"])[:8])


@sync_to_async
def get_finance_totals(user):
    from django.db.models import Sum
    income = Transaction.objects.filter(user=user, type="income").aggregate(total=Sum("amount"))["total"] or Decimal(0)
    expense = Transaction.objects.filter(user=user, type="expense").aggregate(total=Sum("amount"))["total"] or Decimal(0)
    return income, expense


@sync_to_async
def get_upcoming_reminders(user):
    from django.utils import timezone
    now = timezone.now()
    soon = now + timedelta(hours=48)
    return list(
        Reminder.objects.filter(
            user=user, is_active=True, remind_at__gte=now, remind_at__lte=soon
        ).order_by("remind_at")[:5]
    )


# ============================================
# ROUTER + HANDLERS
# ============================================

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)

    if user:
        text = (
            f"سلام {user.first_name or user.username}! 👋\n\n"
            "به ربات <b>Personal Hub</b> خوش آمدید.\n\n"
            "دستورات مفید:\n"
            "• /habits — لیست عادات فعال\n"
            "• /log &lt;نام عادت&gt; — ثبت سریع عادت امروز\n"
            "• /todos — تسک‌های در انتظار\n"
            "• /addtodo &lt;عنوان&gt; — افزودن تسک جدید\n"
            "• /balance — خلاصه مالی\n"
            "• /reminders — یادآورهای ۴۸ ساعت آینده\n"
            "• /help — راهنما"
        )
    else:
        text = (
            "سلام! 👋\n\n"
            "حساب تلگرام شما هنوز به Personal Hub متصل نشده.\n\n"
            "۱. وارد وبسایت یا اپ شوید\n"
            "۲. به بخش پروفایل بروید\n"
            f"۳. این Chat ID را وارد کنید: <code>{chat_id}</code>\n\n"
            "بعد از اتصال، دوباره /start بزنید."
        )

    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📌 <b>دستورات ربات Personal Hub</b>\n\n"
        "/start — شروع و وضعیت اتصال حساب\n"
        "/habits — نمایش عادات فعال\n"
        "/log ورزش — ثبت عادت امروز\n"
        "/todos — لیست تسک‌های در حال انجام\n"
        "/addtodo خرید نان — ایجاد تسک جدید\n"
        "/balance — خلاصه درآمد و هزینه\n"
        "/reminders — یادآورهای نزدیک\n"
        "/help — این پیام"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("habits"))
async def cmd_habits(message: Message):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب شما متصل نیست. لطفاً از وب/اپ Chat ID را وارد کنید.")

    habits = await get_active_habits(user)
    if not habits:
        return await message.answer("هنوز عادتی ثبت نکرده‌اید. از اپ یا وب اضافه کنید.")

    text = "📋 <b>عادات فعال شما:</b>\n\n"
    for h in habits:
        text += f"• {h.name} <i>({h.frequency})</i>\n"
    text += "\nبرای ثبت سریع امروز: <code>/log نام عادت</code>"
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("log"))
async def cmd_log(message: Message, command: CommandObject):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب متصل نیست.")

    if not command.args:
        return await message.answer("استفاده: <code>/log نام عادت</code>\nمثال: <code>/log ورزش</code>")

    habit_name = command.args.strip()

    try:
        habit = await sync_to_async(Habit.objects.get)(
            user=user, name__icontains=habit_name, is_active=True
        )
    except Habit.DoesNotExist:
        return await message.answer(f"عادت «{habit_name}» پیدا نشد.")
    except Habit.MultipleObjectsReturned:
        return await message.answer("چند عادت مشابه پیدا شد. نام دقیق‌تری وارد کنید.")

    today = date.today()
    log, created = await get_or_create_habit_log(habit, today, user)

    status = "ثبت شد ✅" if created else "به‌روزرسانی شد 🔄"
    await message.answer(f"عادت <b>{habit.name}</b> برای امروز {status}!")


@router.message(Command("todos"))
async def cmd_todos(message: Message):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب متصل نیست.")

    todos = await get_pending_todos(user)
    if not todos:
        return await message.answer("🎉 هیچ تسک فعالی نداری. عالیه!")

    text = "✅ <b>تسک‌های در انتظار:</b>\n\n"
    for t in todos:
        due = f" (سررسید: {t.due_date.date()})" if t.due_date else ""
        text += f"• {t.title}{due}\n"
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("addtodo"))
async def cmd_addtodo(message: Message, command: CommandObject):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب متصل نیست.")

    if not command.args:
        return await message.answer("استفاده: <code>/addtodo عنوان تسک</code>")

    title = command.args.strip()
    todo = await create_todo(user, title)
    await message.answer(f"📝 تسک جدید اضافه شد:\n<b>{todo.title}</b>")


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب متصل نیست.")

    income, expense = await get_finance_totals(user)
    balance = income - expense

    text = (
        f"💰 <b>خلاصه مالی شما</b>\n\n"
        f"درآمد کل: <b>+{income:,.0f}</b> IRR\n"
        f"هزینه کل: <b>-{expense:,.0f}</b> IRR\n"
        f"مانده: <b>{balance:,.0f}</b> IRR"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("reminders"))
async def cmd_reminders(message: Message):
    chat_id = message.chat.id
    user = await get_user_from_chat_id(chat_id)
    if not user:
        return await message.answer("❌ حساب متصل نیست.")

    reminders = await get_upcoming_reminders(user)
    if not reminders:
        return await message.answer("در ۴۸ ساعت آینده یادآوری نداری.")

    text = "🔔 <b>یادآورهای نزدیک:</b>\n\n"
    for r in reminders:
        text += f"• {r.title} — {r.remind_at.strftime('%Y-%m-%d %H:%M')}\n"
    await message.answer(text, parse_mode=ParseMode.HTML)


# Fallback for unknown messages
@router.message(F.text)
async def unknown_message(message: Message):
    await message.answer(
        "دستور را متوجه نشدم. از /help برای دیدن لیست دستورات استفاده کنید."
    )


# ============================================
# MAIN RUN FUNCTION
# ============================================

async def main():
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: TELEGRAM_BOT_TOKEN را در settings.py یا متغیر محیطی تنظیم کنید!")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Include our router
    dp.include_router(router)

    print("🤖 Personal Hub Telegram Bot (aiogram 3) در حال اجرا است...")
    await dp.start_polling(bot, allowed_updates=["message"])


def run_bot():
    """Entry point for Django management command"""
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nربات متوقف شد.")


if __name__ == "__main__":
    run_bot()
