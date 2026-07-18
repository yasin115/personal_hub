"""
All routers for the bot are collected here so bot.py just does:

    from telegram_bot.handlers import all_routers
    for r in all_routers:
        dp.include_router(r)

To add a brand new feature area (e.g. "notes"):
  1. Create telegram_bot/handlers/notes.py with its own Router.
  2. Add matching keyboards in telegram_bot/keyboards/inline.py.
  3. Add ORM helpers in telegram_bot/utils.py.
  4. Import + append the router below.
That's it -- nothing else in the bot needs to change.
"""
from .common import router as common_router
from .linking import router as linking_router
from .habits import router as habits_router
from .todos import router as todos_router
from .finance import router as finance_router
from .reminders import router as reminders_router

# Order matters a little: keep `common_router` last among text-catchers so
# specific commands/handlers in feature routers get first refusal, but the
# global "unknown message" fallback in common_router stays last of all.
all_routers = [
    linking_router,
    habits_router,
    todos_router,
    finance_router,
    reminders_router,
    common_router,
]
