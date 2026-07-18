"""
Models for the Telegram bot app.

TelegramLinkCode powers a user-friendly account-linking flow:
1. User sends /start (or taps "🔗 اتصال حساب") in the bot with no linked account.
2. Bot generates a short-lived one-time code and shows it to the user.
3. User enters that code on the website/app (via POST /api/telegram/verify-link/,
   see telegram_bot/views.py) while logged in.
4. The endpoint links request.user's Profile.telegram_chat_id to the code's chat_id.

This keeps the whole linking UX self-contained inside this app -- no changes
needed in `accounts` beyond the `telegram_chat_id` field that already exists there.
"""
import random
import string

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_code() -> str:
    """6-digit numeric code -- easy to read & type on a phone."""
    return "".join(random.choices(string.digits, k=6))


class TelegramLinkCode(models.Model):
    code = models.CharField(max_length=12, unique=True, default=generate_code)
    chat_id = models.BigIntegerField(verbose_name="چت آیدی تلگرام")
    telegram_username = models.CharField(max_length=150, blank=True)
    telegram_first_name = models.CharField(max_length=150, blank=True)

    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="telegram_link_codes"
    )
    used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "کد اتصال تلگرام"
        verbose_name_plural = "کدهای اتصال تلگرام"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} -> chat:{self.chat_id} ({'used' if self.is_used else 'active'})"

    @property
    def is_valid(self) -> bool:
        return (not self.is_used) and timezone.now() <= self.expires_at

    @classmethod
    def create_for_chat(cls, chat_id: int, username: str = "", first_name: str = "", ttl_minutes: int = 10):
        # Invalidate any previous unused codes for this chat to avoid confusion.
        cls.objects.filter(chat_id=chat_id, is_used=False).update(is_used=True, used_at=timezone.now())
        code = generate_code()
        while cls.objects.filter(code=code).exists():
            code = generate_code()
        return cls.objects.create(
            code=code,
            chat_id=chat_id,
            telegram_username=username or "",
            telegram_first_name=first_name or "",
            expires_at=timezone.now() + timezone.timedelta(minutes=ttl_minutes),
        )
