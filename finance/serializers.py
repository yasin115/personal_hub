from rest_framework import serializers
from .models import Transaction, TransactionCategory
from core.utils import get_finance_summary


class TransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = ['id', 'name', 'type', 'icon', 'color', 'is_default']


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'category', 'category_name', 'type', 'amount', 'currency',
            'date', 'description', 'notes', 'payment_method',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("مبلغ باید مثبت باشد.")
        return value
