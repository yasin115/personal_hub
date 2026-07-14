from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'telegram_chat_id', 'timezone', 'language', 'created_at']
    search_fields = ['user__username', 'user__email', 'telegram_chat_id']
    list_filter = ['language', 'timezone']
