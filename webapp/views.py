"""
This app serves a single client-rendered page (webapp/templates/webapp/index.html
+ static/webapp/app.js) that works BOTH as:
  - a normal website (login / register / connect Telegram via QR + deep link), and
  - a Telegram Mini App (opened from inside the bot -- auto-detects
    `Telegram.WebApp.initData` and links the account with zero typing).

All real work (auth, linking) happens client-side against the existing JSON
API (/api/token/, /api/register/, /api/me/, /api/telegram/webhook/...), so
this view just needs to render the page.

IMPORTANT: Telegram Mini Apps are loaded inside an iframe/webview (notably on
Telegram Web/Desktop). Django's default X-Frame-Options: DENY would silently
block that, so this specific view is exempted. Nothing else on the site is
affected. For stricter production hardening, replace this with a
`Content-Security-Policy: frame-ancestors https://web.telegram.org https://t.me;`
header (e.g. via django-csp) instead of a blanket exemption.
"""
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt


@xframe_options_exempt
def index(request):
    return render(request, "webapp/index.html")
