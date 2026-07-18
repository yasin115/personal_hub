#!/usr/bin/env bash
#
# scripts/start_bot.sh
#
# Starts ONLY `manage.py runbot`, detached with nohup. The web app
# (asgi.py) is already running under Passenger and must NOT be started
# here -- see scripts/deploy.sh, which reloads it via restart.txt instead.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
RUN_DIR="$PROJECT_DIR/run"
mkdir -p "$LOG_DIR" "$RUN_DIR"

CONFIG_FILE="$PROJECT_DIR/scripts/cpanel.env"
[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

if [ -n "${VENV_ACTIVATE:-}" ] && [ -f "$VENV_ACTIVATE" ]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
fi
PYTHON_BIN="python"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN="python3"

echo "Starting Telegram bot (runbot) ..."
nohup "$PYTHON_BIN" manage.py runbot >> "$LOG_DIR/bot.log" 2>&1 &
echo $! > "$RUN_DIR/bot.pid"
disown -a 2>/dev/null || true

echo "Bot PID: $(cat "$RUN_DIR/bot.pid")  (logs/bot.log)"
