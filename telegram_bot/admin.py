from django.contrib import admin
from .models import TelegramLinkCode


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "chat_id", "telegram_username", "is_used", "created_at", "expires_at")
    list_filter = ("is_used",)
    search_fields = ("code", "chat_id", "telegram_username")
    readonly_fields = ("created_at",)
