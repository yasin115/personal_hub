"""
Verification for Telegram Mini App (Web App) `initData`.

When a user opens the bot's Mini App button, Telegram gives the page a
signed `initData` string (via `Telegram.WebApp.initData` in JS) containing
the real Telegram user info, HMAC-signed with your bot token. Verifying it
server-side proves who the Telegram user actually is -- no code to type,
no manual step -- which is what powers the automatic linking flow in
views.WebAppLinkView.

This is Telegram's official validation algorithm (documented at
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
and has been stable for a long time, so it's implemented directly here
rather than pulled in as a dependency.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def verify_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400):
    """
    Returns the parsed data dict (with 'user' already json-decoded into a
    dict under key 'user_data') if `init_data` is authentic and fresh,
    otherwise None.
    """
    if not init_data or not bot_token:
        return None

    try:
        pairs = parse_qsl(init_data, strict_parsing=True)
    except ValueError:
        return None

    parsed = dict(pairs)
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    try:
        auth_date = int(parsed.get("auth_date", 0))
    except ValueError:
        return None
    if auth_date <= 0 or (time.time() - auth_date) > max_age_seconds:
        return None  # stale/replayed initData

    user_data = {}
    if "user" in parsed:
        try:
            user_data = json.loads(parsed["user"])
        except (json.JSONDecodeError, TypeError):
            return None

    parsed["user_data"] = user_data
    return parsed
