from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import telegram_bot.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramLinkCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(default=telegram_bot.models.generate_code, max_length=12, unique=True)),
                ("chat_id", models.BigIntegerField(verbose_name="چت آیدی تلگرام")),
                ("telegram_username", models.CharField(blank=True, max_length=150)),
                ("telegram_first_name", models.CharField(blank=True, max_length=150)),
                ("is_used", models.BooleanField(default=False)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "used_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="telegram_link_codes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "کد اتصال تلگرام",
                "verbose_name_plural": "کدهای اتصال تلگرام",
                "ordering": ["-created_at"],
            },
        ),
    ]
