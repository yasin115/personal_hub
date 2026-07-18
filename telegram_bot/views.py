"""
HTTP endpoints for the Telegram bot app.

1. telegram_webhook -- optional webhook receiver if you ever switch from
   polling (`python manage.py runbot`) to webhooks. Polling is what's used
   by default and is simplest for development.

2. VerifyLinkCodeView -- called by the website/app (while the user is
   logged in) with the 6-digit code shown by the bot, to finish linking
   their Personal Hub account to their Telegram chat.

3. UnlinkTelegramView -- lets a logged-in user unlink their Telegram
   account from the website/app side too (mirrors the bot's own
   "قطع اتصال" button in ⚙️ تنظیمات).

NOTE on routing: this app is currently mounted at /api/telegram/webhook/
in personal_hub/urls.py (from the original project scaffold), so the two
endpoints below end up at:
    POST /api/telegram/webhook/verify-link/
    POST /api/telegram/webhook/unlink/
If you'd rather have them at /api/telegram/verify-link/ and
/api/telegram/unlink/, just change the include() prefix for
'telegram_bot.urls' in personal_hub/urls.py to 'api/telegram/' -- nothing
in this app needs to change.
"""
import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import TelegramLinkCode


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


class VerifyLinkCodeView(APIView):
    """POST {"code": "123456"} while authenticated -> links Telegram chat to this user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("code", "")).strip()
        if not code:
            return Response({"detail": "کد را وارد کنید."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            link_code = TelegramLinkCode.objects.get(code=code)
        except TelegramLinkCode.DoesNotExist:
            return Response({"detail": "کد نامعتبر است."}, status=status.HTTP_404_NOT_FOUND)

        if not link_code.is_valid:
            return Response({"detail": "کد منقضی شده یا قبلاً استفاده شده است."}, status=status.HTTP_400_BAD_REQUEST)

        profile = request.user.profile
        profile.telegram_chat_id = link_code.chat_id
        profile.save(update_fields=["telegram_chat_id"])

        link_code.is_used = True
        link_code.used_by = request.user
        link_code.used_at = timezone.now()
        link_code.save(update_fields=["is_used", "used_by", "used_at"])

        return Response({"detail": "حساب تلگرام با موفقیت متصل شد.", "chat_id": link_code.chat_id})


class UnlinkTelegramView(APIView):
    """POST (no body needed) while authenticated -> removes the Telegram link."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        profile.telegram_chat_id = None
        profile.save(update_fields=["telegram_chat_id"])
        return Response({"detail": "اتصال تلگرام قطع شد."})
