from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import BaseModel


class Reminder(BaseModel):
    """
    Flexible reminder system.
    Can be standalone or linked to any object (Habit, Todo, etc.) via GenericForeignKey.
    Supports simple recurrence.
    """
    RECURRENCE_CHOICES = [
        ('none', 'بدون تکرار'),
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('monthly', 'ماهانه'),
        ('custom', 'سفارشی (روز)'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان یادآور")
    description = models.TextField(blank=True)
    
    remind_at = models.DateTimeField(verbose_name="زمان یادآوری")
    is_recurring = models.BooleanField(default=False)
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    recurrence_interval = models.PositiveIntegerField(default=1, help_text="تعداد روز/هفته برای تکرار سفارشی")
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Generic link to other models (Habit, Todo, Transaction, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    is_active = models.BooleanField(default=True)
    last_notified = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "یادآور"
        verbose_name_plural = "یادآورها"
        ordering = ['remind_at']

    def __str__(self):
        return f"{self.title} @ {self.remind_at}"
