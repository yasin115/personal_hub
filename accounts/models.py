from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    Extended user profile.
    Links to Telegram, stores preferences, timezone (important for reminders).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    telegram_chat_id = models.BigIntegerField(
        null=True, blank=True, unique=True,
        help_text="Telegram Chat ID for bot integration. User can set this from app/web."
    )
    timezone = models.CharField(max_length=50, default='Asia/Tehran')
    language = models.CharField(max_length=10, default='fa', choices=[('fa', 'فارسی'), ('en', 'English')])
    
    bio = models.TextField(blank=True, max_length=500)
    avatar_url = models.URLField(blank=True, max_length=500)  # Or use ImageField + media
    
    # Extensible preferences (JSON for future features like notification settings)
    preferences = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پروفایل کاربر"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_telegram_chat_id(self):
        return self.telegram_chat_id


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Auto create Profile when User is created."""
    if created:
        Profile.objects.create(user=instance)
    else:
        # Update if exists
        Profile.objects.get_or_create(user=instance)
