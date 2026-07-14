from django.contrib import admin
from .models import Reminder

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'remind_at', 'is_recurring', 'is_active']
    list_filter = ['is_active', 'is_recurring']
