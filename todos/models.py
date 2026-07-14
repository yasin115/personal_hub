from django.db import models
from core.models import BaseModel


class Todo(BaseModel):
    """
    Todo / Task model with hierarchy support (subtasks via parent).
    Status workflow + priority.
    """
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'پایین'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ سررسید")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Hierarchy
    parent = models.ForeignKey(
        'self', 
        null=True, blank=True, 
        on_delete=models.CASCADE, 
        related_name='subtasks'
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "تسک / todo"
        verbose_name_plural = "تسک‌ها"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def mark_completed(self):
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
