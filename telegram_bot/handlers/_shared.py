"""Small helpers shared across handler modules (kept separate to avoid import cycles)."""
from aiogram.types import Message, CallbackQuery

from ..keyboards.inline import link_account_kb

NOT_LINKED_TEXT = (
    "❌ حساب تلگرام شما هنوز به Personal Hub متصل نشده است.\n\n"
    "برای اتصال، روی دکمه زیر بزنید تا یک کد یکبار مصرف بگیرید و آن را در وبسایت/اپ "
    "در بخش «پروفایل ← اتصال تلگرام» وارد کنید."
)


async def require_linked(target, django_user) -> bool:
    """
    Returns True if the user is linked. Otherwise replies with linking
    instructions (works for both Message and CallbackQuery) and returns False.
    Usage: `if not await require_linked(message, django_user): return`
    """
    if django_user:
        return True

    if isinstance(target, CallbackQuery):
        await target.message.answer(NOT_LINKED_TEXT, reply_markup=link_account_kb())
        await target.answer()
    elif isinstance(target, Message):
        await target.answer(NOT_LINKED_TEXT, reply_markup=link_account_kb())
    return False
