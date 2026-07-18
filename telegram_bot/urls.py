from django.urls import path
from . import views

urlpatterns = [
    path('', views.telegram_webhook, name='telegram_webhook'),
    path('verify-link/', views.VerifyLinkCodeView.as_view(), name='telegram_verify_link'),
    path('unlink/', views.UnlinkTelegramView.as_view(), name='telegram_unlink'),
]
