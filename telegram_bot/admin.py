from django.contrib import admin
from .models import TelegramLinkCode


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("code_short", "user", "chat_id", "telegram_username", "is_used", "created_at", "expires_at")
    list_filter = ("is_used",)
    search_fields = ("code", "chat_id", "telegram_username", "user__username")
    readonly_fields = ("created_at",)

    @admin.display(description="کد")
    def code_short(self, obj):
        return f"{obj.code[:10]}…" if len(obj.code) > 10 else obj.code
