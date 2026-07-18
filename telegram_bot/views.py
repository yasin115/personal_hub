"""
HTTP endpoints for the Telegram bot app.

BEST flow -- Telegram Mini App, zero typing (see the `webapp` Django app):
    0. WebAppLinkView     -> POST, authenticated, body {"init_data": "..."} --
                             called automatically by the Mini App
                             (webapp/static/webapp/app.js) when it detects
                             it's running inside Telegram. Verifies Telegram's
                             signed initData server-side and links the account
                             instantly -- the user never sees a code.

RECOMMENDED flow for a plain browser (not inside Telegram) -- deep link, no typing:
    1. GenerateLinkView   -> POST, authenticated -> returns a deep link + the raw
                             token (front end can render the deep link as a QR
                             code for desktop, and as a plain button/link for
                             mobile -- tapping it opens Telegram directly).
    2. LinkStatusView     -> GET,  authenticated -> front end polls this every
                             ~2s while showing the QR/button; returns
                             {"linked": true/false} so the UI can show
                             "Connected!" the instant the user taps it in
                             Telegram, without any further user action.

FALLBACK flow (manual code, kept for edge cases):
    3. VerifyLinkCodeView -> POST, authenticated, body {"code": "123456"} --
                             for when the user got a code from the bot's
                             /link command and types it into the site instead.

Also:
    4. UnlinkTelegramView -> POST, authenticated -> disconnects Telegram.
    5. telegram_webhook    -> optional webhook receiver (polling is used by
                              default via `python manage.py runbot`).

NOTE on routing: this app is currently mounted at /api/telegram/webhook/ in
personal_hub/urls.py (from the original project scaffold), so these end up at
/api/telegram/webhook/generate-link/, /api/telegram/webhook/link-status/, etc.
If you'd rather have them at /api/telegram/generate-link/ and so on, change
the include() prefix for 'telegram_bot.urls' in personal_hub/urls.py to
'api/telegram/' -- nothing in this app needs to change.

NOTE on TELEGRAM_BOT_USERNAME: GenerateLinkView needs to know your bot's
@username to build the t.me deep link. Set it as an environment variable,
e.g. `export TELEGRAM_BOT_USERNAME=YourBotName` (without the @). You can find
it in @BotFather. This is read directly here so no other file needs touching.
"""
import json
import os

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import TelegramLinkCode
from .webapp_auth import verify_init_data


@csrf_exempt
def telegram_webhook(request):
    """Optional: receive Telegram updates via webhook instead of polling."""
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")
    try:
        update = json.loads(request.body)
        # For simplicity, this project uses polling (`python manage.py runbot`).
        # If you switch to webhooks, dispatch `update` into the aiogram
        # Dispatcher here (requires running an event loop / async view).
        print("Received Telegram update:", update.get("update_id"))
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


class GenerateLinkView(APIView):
    """
    POST while authenticated -> creates a fresh one-time deep-link token and
    returns the ready-to-use https://t.me/... URL. Show this as a button
    (mobile) and/or render it as a QR code (desktop) -- tapping/scanning it
    opens Telegram straight into the bot, which finishes the link
    automatically. No code to type, nothing to copy-paste.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "").lstrip("@")
        if not bot_username:
            return Response(
                {"detail": "TELEGRAM_BOT_USERNAME تنظیم نشده. آن را به‌عنوان متغیر محیطی ست کنید."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        link_code = TelegramLinkCode.create_for_user(request.user)
        deep_link = f"https://t.me/{bot_username}?start=link_{link_code.code}"
        return Response(
            {
                "deep_link": deep_link,
                "expires_at": link_code.expires_at,
                "expires_in_seconds": 600,
            }
        )


class LinkStatusView(APIView):
    """GET while authenticated -> whether Telegram is currently linked. Poll this after showing the QR/button."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response({"linked": bool(profile.telegram_chat_id)})


class VerifyLinkCodeView(APIView):
    """Fallback: POST {"code": "123456"} while authenticated -> links the Telegram chat behind that manual code."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("code", "")).strip()
        if not code:
            return Response({"detail": "کد را وارد کنید."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            link_code = TelegramLinkCode.objects.get(code=code, chat_id__isnull=False)
        except TelegramLinkCode.DoesNotExist:
            return Response({"detail": "کد نامعتبر است."}, status=status.HTTP_404_NOT_FOUND)

        if not link_code.is_valid:
            return Response({"detail": "کد منقضی شده یا قبلاً استفاده شده است."}, status=status.HTTP_400_BAD_REQUEST)

        link_code.complete_with_user(request.user)
        return Response({"detail": "حساب تلگرام با موفقیت متصل شد.", "chat_id": link_code.chat_id})


class WebAppLinkView(APIView):
    """
    POST {"init_data": "<Telegram.WebApp.initData>"} while authenticated ->
    verifies it came from real Telegram (HMAC-signed by the bot token) and
    links the account automatically. This is what the Mini App
    (webapp/static/webapp/app.js) calls when it detects it's running inside
    Telegram -- the user never sees or types a code at all.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        init_data = request.data.get("init_data", "")
        parsed = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        if not parsed:
            return Response(
                {"detail": "داده تلگرام معتبر نیست یا منقضی شده. مینی‌اپ را دوباره باز کنید."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat_id = parsed["user_data"].get("id")
        if not chat_id:
            return Response({"detail": "شناسه کاربر تلگرام یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)

        profile = request.user.profile
        profile.telegram_chat_id = chat_id
        profile.save(update_fields=["telegram_chat_id"])

        return Response({
            "detail": "حساب تلگرام با موفقیت و به‌صورت خودکار متصل شد.",
            "chat_id": chat_id,
            "telegram_first_name": parsed["user_data"].get("first_name", ""),
        })


class UnlinkTelegramView(APIView):
    """POST (no body needed) while authenticated -> removes the Telegram link."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        profile.telegram_chat_id = None
        profile.save(update_fields=["telegram_chat_id"])
        return Response({"detail": "اتصال تلگرام قطع شد."})
