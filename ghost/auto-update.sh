#!/usr/bin/env bash
#
# Ghost auto-update script
#
# Pulls the latest changes from a repo inside the ghost-content volume,
# restarts the ghost-server container, and falls back to the last known
# good commit if the restart fails the health check.
#
# Usage:
#   ./auto-update.sh                  (uses defaults)
#   REPO_PATH=/custom/path ./auto-update.sh
#
# Cron example (every 5 minutes):
#   */5 * * * * /home/user/docker/ghost/auto-update.sh >> /var/log/ghost-auto-update.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="ghost-server"
REPO_PATH="${REPO_PATH:-/var/lib/ghost/content}"
COMPOSE_FILE="${SCRIPT_DIR}/compose.yml"
GOOD_COMMIT_FILE="${SCRIPT_DIR}/last-known-good-commit"

HEALTH_URL="http://localhost:2368/"
HEALTH_RETRIES=5
HEALTH_INITIAL_WAIT=3

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

notify_failure() {
  local message="$1"
  local app_token user_key

  app_token_file="${SCRIPT_DIR}/secrets/pushover_app_token.txt"
  user_key_file="${SCRIPT_DIR}/secrets/pushover_user_key.txt"

  if [[ -f "$app_token_file" && -f "$user_key_file" ]]; then
    app_token="$(cat "$app_token_file")"
    user_key="$(cat "$user_key_file")"
    curl -sf --max-time 10 \
      --form-string "token=${app_token}" \
      --form-string "user=${user_key}" \
      --form-string "title=Ghost Auto-Update Failed" \
      --form-string "message=${message}" \
      --form-string "priority=1" \
      https://api.pushover.net/1/messages.json > /dev/null || true
    log "Pushover notification sent."
  else
    log "Pushover secrets not found, skipping notification."
  fi
}

git_exec() {
  docker exec "$CONTAINER" sh -c "cd ${REPO_PATH} && git $*"
}

health_check() {
  local wait=$HEALTH_INITIAL_WAIT
  for i in $(seq 1 "$HEALTH_RETRIES"); do
    sleep "$wait"
    if docker exec "$CONTAINER" curl -sf --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
      return 0
    fi
    log "Health check attempt ${i}/${HEALTH_RETRIES} failed."
    wait=$((wait * 2))
  done
  return 1
}

restart_ghost() {
  log "Restarting ghost-server..."
  docker compose -f "$COMPOSE_FILE" restart "$CONTAINER"
}

# --- Main ---

log "Starting auto-update check."

# 1. Record current commit before pulling
current_commit="$(git_exec rev-parse HEAD)"
log "Current commit: ${current_commit}"

# 2. Pull latest changes
pull_output="$(git_exec pull 2>&1)" || {
  log "git pull failed: ${pull_output}"
  exit 1
}
log "git pull: ${pull_output}"

if echo "$pull_output" | grep -q "Already up to date"; then
  log "No changes. Exiting."
  exit 0
fi

new_commit="$(git_exec rev-parse HEAD)"
log "New commit: ${new_commit}"

# 3. Restart ghost-server
restart_ghost

# 4. Health check
if health_check; then
  log "Health check passed. Saving ${new_commit} as last known good commit."
  echo "$new_commit" > "$GOOD_COMMIT_FILE"
  exit 0
fi

# 5. Health check failed — fall back
log "Health check failed after update to ${new_commit}."

fallback_commit="${current_commit}"
if [[ -f "$GOOD_COMMIT_FILE" ]]; then
  fallback_commit="$(cat "$GOOD_COMMIT_FILE")"
  log "Using saved last-known-good commit: ${fallback_commit}"
else
  log "No saved good commit. Falling back to pre-pull commit: ${fallback_commit}"
fi

log "Checking out fallback commit ${fallback_commit}..."
git_exec checkout "$fallback_commit" || {
  log "CRITICAL: git checkout of fallback commit failed."
  notify_failure "git checkout ${fallback_commit} failed after bad update to ${new_commit}."
  exit 1
}

restart_ghost

if health_check; then
  log "Fallback to ${fallback_commit} succeeded."
  notify_failure "Auto-update to ${new_commit} failed health check. Rolled back to ${fallback_commit}."
  exit 0
fi

log "CRITICAL: Fallback also failed health check."
notify_failure "Auto-update to ${new_commit} AND fallback to ${fallback_commit} both failed health checks."
exit 1
