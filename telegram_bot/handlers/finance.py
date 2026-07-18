"""Finance: balance summary, recent transactions, and a 5-step add-transaction wizard."""
from datetime import timedelta

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from django.utils import timezone

from ..keyboards.menus import BTN_FINANCE
from ..keyboards.inline import (
    finance_home_kb, transactions_list_kb, tx_type_kb, category_kb, tx_date_kb,
    skip_kb, confirm_kb,
)
from ..states import TransactionCreate
from ..utils import (
    esc, get_finance_totals, list_categories, get_category, create_transaction,
    list_recent_transactions, get_transaction, delete_transaction,
    parse_amount, fmt_money, TX_TYPE_LABEL,
)
from ._shared import require_linked

router = Router(name="finance")
PER_PAGE = 5


@router.message(Command("balance"))
@router.message(F.text == BTN_FINANCE)
async def cmd_balance(message: Message, django_user, state: FSMContext):
    await state.clear()
    if not await require_linked(message, django_user):
        return
    income, expense = await get_finance_totals(django_user)
    balance = income - expense
    text = (
        "💰 <b>خلاصه مالی شما</b>\n"
        "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"🟢 درآمد کل: <b>+{fmt_money(income)}</b>\n"
        f"🔴 هزینه کل: <b>-{fmt_money(expense)}</b>\n"
        f"💼 مانده: <b>{fmt_money(balance)}</b>"
    )
    await message.answer(text, reply_markup=finance_home_kb())


async def _render_recent(target_send, django_user, page: int):
    items, total = await list_recent_transactions(django_user, offset=page * PER_PAGE, limit=PER_PAGE)
    if total == 0:
        await target_send("هنوز تراکنشی ثبت نکرده‌اید.", reply_markup=finance_home_kb())
        return
    text = f"💰 <b>تراکنش‌های اخیر</b> — {total} مورد\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
    await target_send(text, reply_markup=transactions_list_kb(items, page, total, PER_PAGE))


@router.callback_query(F.data.startswith("fin:recent:"))
async def cb_fin_recent(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    page = int(callback.data.split(":")[-1])
    await _render_recent(callback.message.edit_text, django_user, page)
    await callback.answer()


@router.callback_query(F.data.startswith("pg:fin_recent:"))
async def cb_fin_recent_page(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    page = int(callback.data.split(":")[-1])
    await _render_recent(callback.message.edit_text, django_user, page)
    await callback.answer()


@router.callback_query(F.data.startswith("fin:view:"))
async def cb_fin_view(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    tx_id = int(callback.data.split(":")[-1])
    tx = await get_transaction(django_user, tx_id)
    if not tx:
        return await callback.answer("این تراکنش پیدا نشد.", show_alert=True)
    cat = tx.category.name if tx.category else "بدون دسته"
    desc = f"\n{esc(tx.description)}" if tx.description else ""
    await callback.answer(
        f"{TX_TYPE_LABEL.get(tx.type)} | {fmt_money(tx.amount, tx.currency)}\n"
        f"دسته: {cat} | تاریخ: {tx.date}{desc}",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("fin:delask:"))
async def cb_fin_delask(callback: CallbackQuery, django_user):
    if not await require_linked(callback, django_user):
        return
    tx_id = int(callback.data.split(":")[-1])
    tx = await get_transaction(django_user, tx_id)
    if not tx:
        return await callback.answer("این تراکنش پیدا نشد.", show_alert=True)
    await callback.message.answer(
        f"⚠️ آیا از حذف این تراکنش ({fmt_money(tx.amount, tx.currency)}) مطمئن هستید؟",
        reply_markup=confirm_kb(yes_cb=f"fin:delyes:{tx.id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fin:delyes:"))
async def cb_fin_delyes(callback: CallbackQuery, django_user):
    tx_id = int(callback.data.split(":")[-1])
    await delete_transaction(django_user, tx_id)
    await callback.message.edit_text("🗑 تراکنش حذف شد.")
    await callback.answer()


# ---------------- Add transaction wizard ----------------

@router.callback_query(F.data == "fin:add")
async def cb_fin_add_start(callback: CallbackQuery, django_user, state: FSMContext):
    if not await require_linked(callback, django_user):
        return
    await state.set_state(TransactionCreate.type)
    await callback.message.answer("نوع تراکنش را انتخاب کنید:", reply_markup=tx_type_kb())
    await callback.answer()


@router.callback_query(StateFilter(TransactionCreate.type), F.data.startswith("fin:type:"))
async def fin_add_type(callback: CallbackQuery, state: FSMContext):
    tx_type = callback.data.split(":")[-1]
    await state.update_data(type=tx_type)
    await state.set_state(TransactionCreate.amount)
    await callback.message.answer("💵 مبلغ را وارد کنید (فقط عدد، مثال: 250000):")
    await callback.answer()


@router.message(StateFilter(TransactionCreate.amount), F.text)
async def fin_add_amount(message: Message, state: FSMContext, django_user):
    amount = parse_amount(message.text)
    if amount is None:
        return await message.answer("مبلغ نامعتبر است. یک عدد مثبت وارد کنید (مثال: 250000):")
    await state.update_data(amount=str(amount))
    data = await state.get_data()
    categories = await list_categories(django_user, data["type"])
    await state.set_state(TransactionCreate.category)
    await message.answer("🏷 دسته‌بندی را انتخاب کنید:", reply_markup=category_kb(categories))


@router.callback_query(StateFilter(TransactionCreate.category), F.data.startswith("fin:cat:"))
async def fin_add_category(callback: CallbackQuery, state: FSMContext, django_user):
    raw = callback.data.split(":")[-1]
    category = None
    if raw != "none":
        category = await get_category(django_user, int(raw))
    await state.update_data(category_id=category.id if category else None)
    await state.set_state(TransactionCreate.date)
    await callback.message.answer("📅 تاریخ تراکنش:", reply_markup=tx_date_kb())
    await callback.answer()


@router.callback_query(StateFilter(TransactionCreate.date), F.data.startswith("fin:date:"))
async def fin_add_date_quick(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[-1]
    tx_date = timezone.localdate()
    if choice == "yesterday":
        tx_date -= timedelta(days=1)
    await state.update_data(date=tx_date.isoformat())
    await state.set_state(TransactionCreate.description)
    await callback.message.answer(
        "📝 توضیح کوتاهی بنویسید (اختیاری):", reply_markup=skip_kb("fin:desc:skip")
    )
    await callback.answer()


@router.callback_query(StateFilter(TransactionCreate.description), F.data == "fin:desc:skip")
async def fin_add_desc_skip(callback: CallbackQuery, state: FSMContext, django_user):
    await _finish_transaction(callback.message, state, django_user, description="")
    await callback.answer()


@router.message(StateFilter(TransactionCreate.description), F.text)
async def fin_add_desc_text(message: Message, state: FSMContext, django_user):
    await _finish_transaction(message, state, django_user, description=message.text.strip()[:500])


async def _finish_transaction(message: Message, state: FSMContext, django_user, description: str):
    from datetime import date as date_cls
    from decimal import Decimal

    data = await state.get_data()
    category = None
    if data.get("category_id"):
        category = await get_category(django_user, data["category_id"])
    tx = await create_transaction(
        django_user,
        tx_type=data["type"],
        amount=Decimal(data["amount"]),
        category=category,
        tx_date=date_cls.fromisoformat(data["date"]),
        description=description,
    )
    await state.clear()
    sign = "+" if tx.type == "income" else "-"
    await message.answer(f"🎉 تراکنش ثبت شد: {sign}{fmt_money(tx.amount, tx.currency)}")
    income, expense = await get_finance_totals(django_user)
    await message.answer(
        f"💰 مانده جدید: <b>{fmt_money(income - expense)}</b>", reply_markup=finance_home_kb()
    )
