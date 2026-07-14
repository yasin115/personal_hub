"""
Management command to run the Telegram bot with polling.
Usage: python manage.py runbot
"""
import asyncio
from django.core.management.base import BaseCommand
from telegram_bot.bot import run_bot


class Command(BaseCommand):
    help = 'Run the Personal Hub Telegram bot (polling mode)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))
        try:
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Bot stopped by user.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Bot error: {e}'))
