"""
Main URL configuration for Personal Hub API.
All APIs under /api/
JWT auth at /api/token/ and /api/token/refresh/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from accounts.views import RegisterView, MeView  # custom

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User / Profile
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/me/', MeView.as_view(), name='me'),

    # Feature APIs (each app exposes its router)
    path('api/habits/', include('habits.urls')),
    path('api/todos/', include('todos.urls')),
    path('api/reminders/', include('reminders.urls')),
    path('api/finance/', include('finance.urls')),

    # Telegram bot webhook (optional, if you prefer webhook over polling)
    path('api/telegram/webhook/', include('telegram_bot.urls')),
]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
