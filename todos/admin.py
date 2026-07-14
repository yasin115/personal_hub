from django.contrib import admin
from .models import Todo

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['title', 'user__username']
