from django.db import models
from core.models import BaseModel


class Habit(BaseModel):
    """
    Core habit model. User defines habits they want to build.
    Highly extensible: add fields like target_value, unit (e.g. "5 glasses of water"), etc.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('custom', 'سفارشی'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="نام عادت")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        default='daily',
        verbose_name="فرکانس"
    )
    target_per_period = models.PositiveIntegerField(default=1, verbose_name="تعداد هدف در هر دوره")
    period_days = models.PositiveIntegerField(default=1, verbose_name="تعداد روزهای دوره (برای سفارشی)")
    
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name="رنگ (هگز)")
    icon = models.CharField(max_length=50, blank=True, verbose_name="آیکون/ایموجی")  # e.g. "💧" or "fa-running"
    
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "عادت"
        verbose_name_plural = "عادات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class HabitLog(BaseModel):
    """
    Daily/periodic log of habit completion.
    One log per habit per date (enforced by unique_together).
    Supports count for habits like "drink 8 glasses".
    """
    habit = models.ForeignKey(
        Habit, 
        on_delete=models.CASCADE, 
        related_name='logs',
        verbose_name="عادت"
    )
    date = models.DateField(verbose_name="تاریخ")
    completed = models.BooleanField(default=False, verbose_name="انجام شده؟")
    count = models.PositiveIntegerField(default=0, verbose_name="تعداد انجام شده")
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    
    class Meta:
        verbose_name = "ثبت عادت"
        verbose_name_plural = "ثبت‌های عادت"
        unique_together = ('habit', 'date')
        ordering = ['-date']

    def __str__(self):
        status = "✓" if self.completed else "✗"
        return f"{self.habit.name} - {self.date} {status}"
