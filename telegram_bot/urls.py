from django.urls import path
from . import views

urlpatterns = [
    path('', views.telegram_webhook, name='telegram_webhook'),

    # Mini App -- zero-typing auto-link via signed Telegram initData
    path('webapp-link/', views.WebAppLinkView.as_view(), name='telegram_webapp_link'),

    # Plain browser -- deep link + QR (no typing) and status polling
    path('generate-link/', views.GenerateLinkView.as_view(), name='telegram_generate_link'),
    path('link-status/', views.LinkStatusView.as_view(), name='telegram_link_status'),

    # Fallback -- manual numeric code typed on the site
    path('verify-link/', views.VerifyLinkCodeView.as_view(), name='telegram_verify_link'),

    path('unlink/', views.UnlinkTelegramView.as_view(), name='telegram_unlink'),
]
