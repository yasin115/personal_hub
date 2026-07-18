"""Reminders: list, toggle, delete, and a 3-step add wizard (title -> when -> recurrence)."""
from datetime import timedelta, datetime as dt

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from django.utils import timezone

from ..keyboards.menus import BTN_REMINDERS
from ..keyboards.inline import (
    reminders_list_kb, reminder_quick_time_kb, reminder_recurrence_kb, confirm_kb,
)
from ..states import ReminderCreate
from ..utils import (
    esc, list_reminders, get_reminder, create_reminder, toggle_reminder_active,
    delete_reminder, parse_simple_datetime, fmt_dt, RECURRENCE_LABEL,
)
from ._shared import require_linked

router = Router(name="reminders")
PER_PAGE = 5


async def _render_list(target_send, django_user, page: int):
    items, total = await list_reminders(django_user, offset=page * PER_PAGE, limit=PER_PAGE)
    if total == 0:
        await target_send(
            "در ۴۸ ساعت آینده یادآوری فعالی نداری.\nبرای افزودن، دکمه زیر را بزن.",
            reply_markup=reminders_list_kb([], 0, 0, PER_PAGE),
        )
        return
    text = f"⏰ <b>یادآورهای آینده</b> — {total} مورد\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
    await target_send(text, reply_markup=reminders_list_kb(items, page, total, PER_PAGE))


@router.message(Command("reminders"))
@router.message(F.text == BTN_REMINDERS)
async def cmd_reminders(message: Message, django_user, state: FSMContext):
    await state.clear()
    if not await require_linked(message, django_user):
        return
    await _render_list(message.answer, django_user, page=0)


@router.callback_query(F.data.startswith("pg:reminders:"))
async def cb_reminders_page(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    page = int(callback.data.split(":")[-1])
    await _render_list(callback.message.edit_text, django_user, page)
    await callback.answer()


@router.callback_query(F.data.startswith("rm:view:"))
async def cb_reminder_view(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    reminder_id = int(callback.data.split(":")[-1])
    r = await get_reminder(django_user, reminder_id)
    if not r:
        return await callback.answer("این یادآور پیدا نشد.", show_alert=True)
    await callback.answer(
        f"🔔 {r.title}\n⏰ {fmt_dt(r.remind_at)}\n🔁 {RECURRENCE_LABEL.get(r.recurrence_type)}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("rm:toggle:"))
async def cb_reminder_toggle(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    reminder_id = int(callback.data.split(":")[-1])
    r = await toggle_reminder_active(django_user, reminder_id)
    if not r:
        return await callback.answer("این یادآور پیدا نشد.", show_alert=True)
    await callback.answer("فعال شد ✅" if r.is_active else "غیرفعال شد ⏸")
    await _render_list(callback.message.edit_text, django_user, page=0)


@router.callback_query(F.data.startswith("rm:delask:"))
async def cb_reminder_delask(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    reminder_id = int(callback.data.split(":")[-1])
    r = await get_reminder(django_user, reminder_id)
    if not r:
        return await callback.answer("این یادآور پیدا نشد.", show_alert=True)
    await callback.message.answer(
        f"⚠️ آیا از حذف یادآور «{esc(r.title)}» مطمئن هستید؟",
        reply_markup=confirm_kb(yes_cb=f"rm:delyes:{r.id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rm:delyes:"))
async def cb_reminder_delyes(callback: CallbackQuery, django_user):
    reminder_id = int(callback.data.split(":")[-1])
    await delete_reminder(django_user, reminder_id)
    await callback.message.edit_text("🗑 یادآور حذف شد.")
    await callback.answer()


# ---------------- Add reminder wizard ----------------

@router.callback_query(F.data == "rm:add")
async def cb_reminder_add_start(callback: CallbackQuery, django_user, state: FSMContext):
    if not await require_linked(callback, django_user):
        return
    await state.set_state(ReminderCreate.title)
    await callback.message.answer("✍️ عنوان یادآور را بنویسید:")
    await callback.answer()


@router.message(StateFilter(ReminderCreate.title), F.text)
async def reminder_add_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title or len(title) > 255:
        return await message.answer("عنوان نامعتبر است. دوباره بنویسید:")
    await state.update_data(title=title)
    await state.set_state(ReminderCreate.when)
    await message.answer("⏰ چه زمانی یادآوری شود؟", reply_markup=reminder_quick_time_kb())


@router.callback_query(StateFilter(ReminderCreate.when), F.data.startswith("rm:when:"))
async def reminder_add_when(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[-1]
    now = timezone.localtime(timezone.now())

    if choice == "manual":
        await callback.message.answer(
            "🗓 زمان را به شکل <code>YYYY-MM-DD HH:MM</code> بنویسید (مثال: 2026-07-20 09:00):"
        )
        return await callback.answer()

    remind_at = None
    if choice == "1h":
        remind_at = now + timedelta(hours=1)
    elif choice == "tonight":
        remind_at = now.replace(hour=18, minute=0, second=0, microsecond=0)
        if remind_at <= now:
            remind_at += timedelta(days=1)
    elif choice == "tomorrow_morning":
        remind_at = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    await state.update_data(remind_at=remind_at.isoformat())
    await state.set_state(ReminderCreate.recurrence)
    await callback.message.answer("🔁 آیا این یادآور تکرار شود؟", reply_markup=reminder_recurrence_kb())
    await callback.answer()


@router.message(StateFilter(ReminderCreate.when), F.text)
async def reminder_add_when_manual(message: Message, state: FSMContext):
    remind_at = parse_simple_datetime(message.text)
    if not remind_at:
        return await message.answer(
            "فرمت زمان را متوجه نشدم. به شکل <code>YYYY-MM-DD HH:MM</code> بنویسید:"
        )
    await state.update_data(remind_at=remind_at.isoformat())
    await state.set_state(ReminderCreate.recurrence)
    await message.answer("🔁 آیا این یادآور تکرار شود؟", reply_markup=reminder_recurrence_kb())


@router.callback_query(StateFilter(ReminderCreate.recurrence), F.data.startswith("rm:rec:"))
async def reminder_add_recurrence(callback: CallbackQuery, state: FSMContext, django_user):
    recurrence = callback.data.split(":")[-1]
    data = await state.get_data()
    remind_at = dt.fromisoformat(data["remind_at"])
    r = await create_reminder(django_user, data["title"], remind_at, recurrence)
    await state.clear()
    await callback.message.answer(
        f"🎉 یادآور «{esc(r.title)}» برای {fmt_dt(r.remind_at)} ثبت شد!"
    )
    await _render_list(callback.message.answer, django_user, page=0)
    await callback.answer()
