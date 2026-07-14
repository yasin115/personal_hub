from django.contrib import admin
from .models import Habit, HabitLog


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'frequency', 'is_active', 'created_at']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'user__username']


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ['habit', 'date', 'completed', 'count', 'created_at']
    list_filter = ['completed', 'date']
    search_fields = ['habit__name']
