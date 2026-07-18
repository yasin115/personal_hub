"""Habits: list, quick-log, stats, toggle active, delete, and a 3-step add wizard."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..keyboards.menus import BTN_HABITS
from ..keyboards.inline import (
    habits_list_kb, habit_frequency_kb, skip_kb, confirm_kb,
)
from ..states import HabitCreate
from ..utils import (
    esc, list_habits, get_habit, create_habit, toggle_habit_active,
    delete_habit, log_habit_today, habit_stats, FREQUENCY_LABEL,
)
from ._shared import require_linked

router = Router(name="habits")
PER_PAGE = 5


async def _render_list(target_send, django_user, page: int):
    habits, total = await list_habits(django_user, active_only=False, offset=page * PER_PAGE, limit=PER_PAGE)
    if total == 0:
        await target_send(
            "هنوز عادتی ثبت نکرده‌اید 🙂\nبرای شروع، دکمه زیر را بزنید.",
            reply_markup=habits_list_kb([], 0, 0, PER_PAGE),
        )
        return
    text = f"📋 <b>عادات شما</b> — {total} مورد\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
    await target_send(text, reply_markup=habits_list_kb(habits, page, total, PER_PAGE))


@router.message(Command("habits"))
@router.message(F.text == BTN_HABITS)
async def cmd_habits(message: Message, django_user, state: FSMContext):
    await state.clear()
    if not await require_linked(message, django_user):
        return
    await _render_list(message.answer, django_user, page=0)


@router.callback_query(F.data.startswith("pg:habits:"))
async def cb_habits_page(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    page = int(callback.data.split(":")[-1])
    await callback.message.edit_text("📋 در حال بارگذاری...")
    await _render_list(callback.message.edit_text, django_user, page)
    await callback.answer()


@router.callback_query(F.data.startswith("hb:view:"))
async def cb_habit_view(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    habit_id = int(callback.data.split(":")[-1])
    habit = await get_habit(django_user, habit_id)
    if not habit:
        return await callback.answer("این عادت پیدا نشد.", show_alert=True)
    state_text = "فعال ✅" if habit.is_active else "غیرفعال ⏸"
    await callback.answer(
        f"{habit.icon or '•'} {habit.name}\n"
        f"فرکانس: {FREQUENCY_LABEL.get(habit.frequency, habit.frequency)}\n"
        f"وضعیت: {state_text}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("hb:log:"))
async def cb_habit_log(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    habit_id = int(callback.data.split(":")[-1])
    habit = await get_habit(django_user, habit_id)
    if not habit:
        return await callback.answer("این عادت پیدا نشد.", show_alert=True)
    log, created = await log_habit_today(habit, django_user)
    msg = "ثبت شد ✅" if created else f"به‌روزرسانی شد 🔄 (تعداد امروز: {log.count})"
    await callback.answer(f"«{habit.name}» {msg}", show_alert=False)


@router.callback_query(F.data.startswith("hb:stats:"))
async def cb_habit_stats(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    habit_id = int(callback.data.split(":")[-1])
    habit = await get_habit(django_user, habit_id)
    if not habit:
        return await callback.answer("این عادت پیدا نشد.", show_alert=True)
    count_30 = await habit_stats(habit, days=30)
    count_7 = await habit_stats(habit, days=7)
    await callback.answer(
        f"📊 «{habit.name}»\n۷ روز اخیر: {count_7} بار\n۳۰ روز اخیر: {count_30} بار",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("hb:toggle:"))
async def cb_habit_toggle(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    habit_id = int(callback.data.split(":")[-1])
    habit = await toggle_habit_active(django_user, habit_id)
    if not habit:
        return await callback.answer("این عادت پیدا نشد.", show_alert=True)
    state_text = "فعال شد ✅" if habit.is_active else "غیرفعال شد ⏸"
    await callback.answer(f"«{habit.name}» {state_text}")
    await _render_list(callback.message.edit_text, django_user, page=0)


@router.callback_query(F.data.startswith("hb:delask:"))
async def cb_habit_delask(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    habit_id = int(callback.data.split(":")[-1])
    habit = await get_habit(django_user, habit_id)
    if not habit:
        return await callback.answer("این عادت پیدا نشد.", show_alert=True)
    await callback.message.answer(
        f"⚠️ آیا از حذف عادت «{esc(habit.name)}» مطمئن هستید؟ این کار همه سوابق ثبت‌شده را هم پاک می‌کند.",
        reply_markup=confirm_kb(yes_cb=f"hb:delyes:{habit.id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hb:delyes:"))
async def cb_habit_delyes(callback: CallbackQuery, django_user):
    habit_id = int(callback.data.split(":")[-1])
    await delete_habit(django_user, habit_id)
    await callback.message.edit_text("🗑 عادت حذف شد.")
    await callback.answer()


# ---------------- Add habit wizard ----------------

@router.callback_query(F.data == "hb:add")
async def cb_habit_add_start(callback: CallbackQuery, django_user, state: FSMContext):
    if not await require_linked(callback, django_user):
        return
    await state.set_state(HabitCreate.name)
    await callback.message.answer(
        "✍️ نام عادت جدید را بنویسید (مثال: نوشیدن آب، مطالعه، ورزش):"
    )
    await callback.answer()


@router.message(StateFilter(HabitCreate.name), F.text)
async def habit_add_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) > 200:
        return await message.answer("نام نامعتبر است. یک نام کوتاه‌تر بنویسید:")
    await state.update_data(name=name)
    await state.set_state(HabitCreate.frequency)
    await message.answer("⏱ فرکانس این عادت چیست؟", reply_markup=habit_frequency_kb())


@router.callback_query(StateFilter(HabitCreate.frequency), F.data.startswith("hb:freq:"))
async def habit_add_frequency(callback: CallbackQuery, state: FSMContext):
    freq = callback.data.split(":")[-1]
    await state.update_data(frequency=freq)
    await state.set_state(HabitCreate.icon)
    await callback.message.answer(
        "یک ایموجی برای این عادت بفرستید (مثلاً 💧 یا 🏃) یا رد کنید:",
        reply_markup=skip_kb("hb:icon:skip"),
    )
    await callback.answer()


@router.callback_query(StateFilter(HabitCreate.icon), F.data == "hb:icon:skip")
async def habit_add_icon_skip(callback: CallbackQuery, state: FSMContext, django_user):
    await _finish_habit(callback.message, state, django_user, icon="")
    await callback.answer()


@router.message(StateFilter(HabitCreate.icon), F.text)
async def habit_add_icon(message: Message, state: FSMContext, django_user):
    icon = message.text.strip()[:10]
    await _finish_habit(message, state, django_user, icon=icon)


async def _finish_habit(message: Message, state: FSMContext, django_user, icon: str):
    data = await state.get_data()
    habit = await create_habit(django_user, data["name"], data["frequency"], icon)
    await state.clear()
    await message.answer(
        f"🎉 عادت «{esc(habit.name)}» ({FREQUENCY_LABEL.get(habit.frequency, habit.frequency)}) ساخته شد!"
    )
    await _render_list(message.answer, django_user, page=0)
