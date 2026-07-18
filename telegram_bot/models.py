"""
Models for the Telegram bot app.

TelegramLinkCode powers account linking, two ways:

PRIMARY -- deep link, zero typing (recommended, use this in the site/app UI):
1. Logged-in user taps "Connect Telegram" on the site/app.
2. Site calls POST /api/telegram/webhook/generate-link/ (see views.py) ->
   gets back a `https://t.me/<bot>?start=link_<token>` URL.
3. Site shows that as a button (mobile: opens Telegram directly) and/or a
   QR code (desktop: scan with phone camera).
4. User taps the link / scans the QR -> Telegram opens the bot and
   auto-sends "/start link_<token>" -- no typing, nothing to copy-paste.
5. The bot's deep-link handler (handlers/linking.py) reads the token, and
   because the bot runs in the same Django process/DB, links
   Profile.telegram_chat_id directly -- no HTTP round-trip needed.
6. Site polls GET /api/telegram/webhook/link-status/ every couple seconds
   and shows "Connected!" the moment it's done.

FALLBACK -- manual code (kept for edge cases, e.g. deep links not opening
Telegram properly on some browser/OS combos):
1. User sends /link inside the bot -> bot shows a short numeric code.
2. User types that code into the site (POST .../verify-link/) while logged in.

Both flows write to the same Profile.telegram_chat_id field already defined
in the `accounts` app -- no changes needed there.
"""
import random
import secrets
import string
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_bot_code() -> str:
    """6-digit numeric code -- for the manual fallback flow, easy to type by hand."""
    return "".join(random.choices(string.digits, k=6))


def generate_deeplink_token() -> str:
    """
    URL-safe token for the deep-link flow. Never typed by a human -- only
    embedded in a link/QR code -- so it can (and should) be long and
    effectively unguessable, unlike the short manual code above.
    """
    return secrets.token_urlsafe(16)


class TelegramLinkCode(models.Model):
    code = models.CharField(max_length=64, unique=True)

    # Deep-link flow: set at creation time (site knows who's asking).
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="telegram_link_codes"
    )
    # Manual flow: set at creation time (bot knows the chat_id already).
    # Deep-link flow: filled in later, once the bot receives the /start payload.
    chat_id = models.BigIntegerField(null=True, blank=True, verbose_name="چت آیدی تلگرام")

    telegram_username = models.CharField(max_length=150, blank=True)
    telegram_first_name = models.CharField(max_length=150, blank=True)

    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "کد اتصال تلگرام"
        verbose_name_plural = "کدهای اتصال تلگرام"
        ordering = ["-created_at"]

    def __str__(self):
        who = self.user_id or self.chat_id or "?"
        return f"{self.code[:8]}... -> {who} ({'used' if self.is_used else 'active'})"

    @property
    def is_valid(self) -> bool:
        return (not self.is_used) and timezone.now() <= self.expires_at

    # ---- creation ----

    @classmethod
    def create_for_user(cls, user: User, ttl_minutes: int = 10):
        """Site/app-initiated (deep-link flow). Called when a logged-in user taps 'Connect Telegram'."""
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        token = generate_deeplink_token()
        return cls.objects.create(code=token, user=user, expires_at=timezone.now() + timedelta(minutes=ttl_minutes))

    @classmethod
    def create_for_chat(cls, chat_id: int, username: str = "", first_name: str = "", ttl_minutes: int = 10):
        """Bot-initiated (manual fallback flow). Called by the bot's /link command."""
        cls.objects.filter(chat_id=chat_id, is_used=False, user__isnull=True).update(is_used=True)
        code = generate_bot_code()
        while cls.objects.filter(code=code).exists():
            code = generate_bot_code()
        return cls.objects.create(
            code=code,
            chat_id=chat_id,
            telegram_username=username or "",
            telegram_first_name=first_name or "",
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    # ---- completion ----

    def complete_with_chat(self, chat_id: int, username: str = "", first_name: str = ""):
        """Deep-link flow: the bot calls this once it receives the matching /start payload."""
        self.chat_id = chat_id
        self.telegram_username = username or ""
        self.telegram_first_name = first_name or ""
        self.is_used = True
        self.save(update_fields=["chat_id", "telegram_username", "telegram_first_name", "is_used"])
        profile = self.user.profile
        profile.telegram_chat_id = chat_id
        profile.save(update_fields=["telegram_chat_id"])

    def complete_with_user(self, user: User):
        """Manual flow: the site's verify-link endpoint calls this once the user types the code."""
        self.user = user
        self.is_used = True
        self.save(update_fields=["user", "is_used"])
        profile = user.profile
        profile.telegram_chat_id = self.chat_id
        profile.save(update_fields=["telegram_chat_id"])
