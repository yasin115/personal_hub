#!/usr/bin/env bash
#
# scripts/deploy.sh  (cPanel / Passenger hosting)
#
# Checks GitHub (origin/main) for new commits. If there are any:
#   - pulls the changes (replaces modified files, adds new ones, removes
#     deleted ones) with `git reset --hard`
#   - installs/updates requirements.txt INSIDE the cPanel virtualenv
#   - runs Django migrations
#   - reloads the web app (asgi.py) by touching Passenger's restart.txt --
#     Passenger itself handles stopping/starting that process, we never
#     kill it directly
#   - stops and restarts the Telegram bot (runbot) with nohup, since that
#     process is NOT managed by Passenger
#
# If there's nothing new, it does nothing except log that fact.
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
RUN_DIR="$PROJECT_DIR/run"
mkdir -p "$LOG_DIR" "$RUN_DIR"

DEPLOY_LOG="$LOG_DIR/deploy.log"
RESULT_FILE="$RUN_DIR/deploy_result"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$DEPLOY_LOG"; }

# --- load per-host config (APP_ROOT, VENV_ACTIVATE, PASSENGER_RESTART_FILE) ---
CONFIG_FILE="$PROJECT_DIR/scripts/cpanel.env"
if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: scripts/cpanel.env not found -- copy scripts/cpanel.env.example and fill it in."
    echo "ERROR:missing_config" > "$RESULT_FILE"
    exit 1
fi
# shellcheck disable=SC1090
source "$CONFIG_FILE"

if [ -f "$VENV_ACTIVATE" ]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
else
    log "WARNING: VENV_ACTIVATE ($VENV_ACTIVATE) not found -- falling back to system python3."
fi
PYTHON_BIN="python"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN="python3"

log "=== deploy started ==="

BRANCH="main"

if ! git fetch origin "$BRANCH" >> "$DEPLOY_LOG" 2>&1; then
    log "ERROR: git fetch failed -- check network/remote access."
    echo "ERROR:fetch_failed" > "$RESULT_FILE"
    exit 1
fi

LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    log "Already up to date ($LOCAL_HASH). Nothing to do."
    echo "NO_UPDATE" > "$RESULT_FILE"
    exit 0
fi

log "Update found: $LOCAL_HASH -> $REMOTE_HASH"

# Hard-reset to origin: replaces changed files, adds new ones, removes
# files that were deleted upstream. db.sqlite3 / .env / logs / run /
# cpanel.env are all gitignored so they are untouched by this.
git reset --hard "origin/$BRANCH" >> "$DEPLOY_LOG" 2>&1
git clean -fd --exclude=logs --exclude=run --exclude=db.sqlite3 --exclude=.env --exclude=scripts/cpanel.env >> "$DEPLOY_LOG" 2>&1

log "Installing/updating dependencies in venv..."
"$PYTHON_BIN" -m pip install -r requirements.txt >> "$DEPLOY_LOG" 2>&1

log "Applying migrations..."
"$PYTHON_BIN" manage.py migrate --noinput >> "$DEPLOY_LOG" 2>&1

log "Collecting static files..."
"$PYTHON_BIN" manage.py collectstatic --noinput >> "$DEPLOY_LOG" 2>&1 || true

log "Restarting Telegram bot (runbot)..."
bash "$PROJECT_DIR/scripts/stop_bot.sh" >> "$DEPLOY_LOG" 2>&1
sleep 2
bash "$PROJECT_DIR/scripts/start_bot.sh" >> "$DEPLOY_LOG" 2>&1

log "Reloading web app via Passenger (touching restart.txt)..."
mkdir -p "$(dirname "$PASSENGER_RESTART_FILE")"
touch "$PASSENGER_RESTART_FILE"

echo "UPDATED:$LOCAL_HASH:$REMOTE_HASH" > "$RESULT_FILE"
log "=== deploy finished ==="
