"""Todos: list, complete, delete, and a 3-step add wizard (title -> priority -> due date)."""
from datetime import timedelta, datetime as dt

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from django.utils import timezone

from ..keyboards.menus import BTN_TODOS
from ..keyboards.inline import todos_list_kb, todo_priority_kb, todo_due_date_kb, confirm_kb
from ..states import TodoCreate
from ..utils import (
    esc, list_todos, get_todo, create_todo, complete_todo, delete_todo,
    parse_simple_date, PRIORITY_LABEL,
)
from ._shared import require_linked

router = Router(name="todos")
PER_PAGE = 5


async def _render_list(target_send, django_user, page: int):
    todos, total = await list_todos(django_user, offset=page * PER_PAGE, limit=PER_PAGE)
    if total == 0:
        await target_send(
            "🎉 هیچ کار در انتظاری نداری!\nبرای افزودن یک کار جدید، دکمه زیر را بزن.",
            reply_markup=todos_list_kb([], 0, 0, PER_PAGE),
        )
        return
    text = f"✅ <b>کارهای در انتظار</b> ({total} مورد)"
    await target_send(text, reply_markup=todos_list_kb(todos, page, total, PER_PAGE))


@router.message(Command("todos"))
@router.message(F.text == BTN_TODOS)
async def cmd_todos(message: Message, django_user, state: FSMContext):
    await state.clear()
    if not await require_linked(message, django_user):
        return
    await _render_list(message.answer, django_user, page=0)


@router.callback_query(F.data.startswith("pg:todos:"))
async def cb_todos_page(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    page = int(callback.data.split(":")[-1])
    await _render_list(callback.message.edit_text, django_user, page)
    await callback.answer()


@router.callback_query(F.data.startswith("td:view:"))
async def cb_todo_view(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    todo_id = int(callback.data.split(":")[-1])
    todo = await get_todo(django_user, todo_id)
    if not todo:
        return await callback.answer("این کار پیدا نشد.", show_alert=True)
    due = f"\n📅 سررسید: {todo.due_date.strftime('%Y-%m-%d')}" if todo.due_date else ""
    desc = f"\n\n{esc(todo.description)}" if todo.description else ""
    await callback.answer(
        f"{PRIORITY_LABEL.get(todo.priority, '')} {todo.title}{due}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("td:done:"))
async def cb_todo_done(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    todo_id = int(callback.data.split(":")[-1])
    todo = await complete_todo(django_user, todo_id)
    if not todo:
        return await callback.answer("این کار پیدا نشد.", show_alert=True)
    await callback.answer(f"✅ «{todo.title}» تکمیل شد!")
    await _render_list(callback.message.edit_text, django_user, page=0)


@router.callback_query(F.data.startswith("td:delask:"))
async def cb_todo_delask(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    todo_id = int(callback.data.split(":")[-1])
    todo = await get_todo(django_user, todo_id)
    if not todo:
        return await callback.answer("این کار پیدا نشد.", show_alert=True)
    await callback.message.answer(
        f"⚠️ آیا از حذف «{esc(todo.title)}» مطمئن هستید؟",
        reply_markup=confirm_kb(yes_cb=f"td:delyes:{todo.id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("td:delyes:"))
async def cb_todo_delyes(callback: CallbackQuery, django_user):
    todo_id = int(callback.data.split(":")[-1])
    await delete_todo(django_user, todo_id)
    await callback.message.edit_text("🗑 کار حذف شد.")
    await callback.answer()


# ---------------- Add todo wizard ----------------

@router.callback_query(F.data == "td:add")
async def cb_todo_add_start(callback: CallbackQuery, django_user, state: FSMContext):
    if not await require_linked(callback, django_user):
        return
    await state.set_state(TodoCreate.title)
    await callback.message.answer("✍️ عنوان کار جدید را بنویسید:")
    await callback.answer()


@router.message(StateFilter(TodoCreate.title), F.text)
async def todo_add_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title or len(title) > 255:
        return await message.answer("عنوان نامعتبر است. دوباره بنویسید:")
    await state.update_data(title=title)
    await state.set_state(TodoCreate.priority)
    await message.answer("🎯 اولویت این کار چقدر است؟", reply_markup=todo_priority_kb())


@router.callback_query(StateFilter(TodoCreate.priority), F.data.startswith("td:pri:"))
async def todo_add_priority(callback: CallbackQuery, state: FSMContext):
    priority = callback.data.split(":")[-1]
    await state.update_data(priority=priority)
    await state.set_state(TodoCreate.due_date)
    await callback.message.answer("📅 سررسید این کار چه زمانی است؟", reply_markup=todo_due_date_kb())
    await callback.answer()


@router.callback_query(StateFilter(TodoCreate.due_date), F.data.startswith("td:due:"))
async def todo_add_due_quick(callback: CallbackQuery, state: FSMContext, django_user):
    choice = callback.data.split(":")[-1]
    due_date = None
    if choice == "today":
        due_date = timezone.now()
    elif choice == "tomorrow":
        due_date = timezone.now() + timedelta(days=1)
    await _finish_todo(callback.message, state, django_user, due_date)
    await callback.answer()


@router.message(StateFilter(TodoCreate.due_date), F.text)
async def todo_add_due_text(message: Message, state: FSMContext, django_user):
    parsed = parse_simple_date(message.text)
    if not parsed:
        return await message.answer(
            "فرمت تاریخ را متوجه نشدم. از دکمه‌ها استفاده کنید یا به شکل YYYY-MM-DD بنویسید:"
        )
    due_dt = timezone.make_aware(dt.combine(parsed, dt.min.time()))
    await _finish_todo(message, state, django_user, due_dt)


async def _finish_todo(message: Message, state: FSMContext, django_user, due_date):
    data = await state.get_data()
    todo = await create_todo(django_user, data["title"], data["priority"], due_date)
    await state.clear()
    due_txt = f" | سررسید: {due_date.strftime('%Y-%m-%d')}" if due_date else ""
    await message.answer(f"🎉 کار «{esc(todo.title)}» اضافه شد!{due_txt}")
    await _render_list(message.answer, django_user, page=0)
