from django.contrib import admin
from .models import Transaction, TransactionCategory

@admin.register(TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user', 'is_default']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['type', 'amount', 'currency', 'category', 'date', 'user']
    list_filter = ['type', 'date']
