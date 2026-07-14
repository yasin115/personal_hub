from django.db import models
from decimal import Decimal
from core.models import BaseModel


class TransactionCategory(BaseModel):
    """
    User-defined or default categories for income/expense.
    type: income, expense or both.
    """
    TYPE_CHOICES = [
        ('income', 'درآمد'),
        ('expense', 'هزینه'),
        ('both', 'هر دو'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='expense')
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#EF4444')
    is_default = models.BooleanField(default=False)  # system defaults have user=None sometimes

    class Meta:
        verbose_name = "دسته‌بندی تراکنش"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Transaction(BaseModel):
    """
    Income and Expense tracking.
    """
    TYPE_CHOICES = [
        ('income', 'درآمد'),
        ('expense', 'هزینه'),
    ]
    
    category = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='transactions'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="مبلغ")
    currency = models.CharField(max_length=10, default='IRR', verbose_name="واحد پول")
    date = models.DateField(verbose_name="تاریخ تراکنش")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True, verbose_name="روش پرداخت")

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        ordering = ['-date', '-created_at']

    def __str__(self):
        sign = '+' if self.type == 'income' else '-'
        return f"{sign}{self.amount} {self.currency} | {self.description[:30] if self.description else self.category}"
