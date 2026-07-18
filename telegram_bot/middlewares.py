"""
Middleware that resolves the Django user for every incoming update once,
and injects it into handler data as `django_user` (or None if not linked).

This removes the "get_user_from_chat_id + if not user: ..." boilerplate that
used to be repeated in every single handler.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from .utils import get_user_from_chat_id


class DjangoUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_id = None
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id if event.message else event.from_user.id

        data["django_user"] = await get_user_from_chat_id(chat_id) if chat_id else None
        return await handler(event, data)
