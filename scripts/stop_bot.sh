#!/usr/bin/env bash
#
# scripts/stop_bot.sh
#
# Stops the runbot process started by scripts/start_bot.sh. Does NOT touch
# the web app -- that's Passenger's job (see deploy.sh's restart.txt step).
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$PROJECT_DIR/run"
PIDFILE="$RUN_DIR/bot.pid"

if [ -f "$PIDFILE" ]; then
    pid=$(cat "$PIDFILE" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        sleep 1
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PIDFILE"
fi

# Fallback in case the pidfile was stale/missing.
pkill -f "manage.py runbot" 2>/dev/null || true

exit 0
