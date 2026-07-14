from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    """
    Abstract base model for most user-owned objects.
    Provides user FK + timestamps.
    Inherit from this in habits, todos, finance, reminders for consistency and easy extension.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='%(class)ss'  # e.g. habits, todos
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"
