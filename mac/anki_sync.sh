#!/usr/bin/env bash
# Mac side: pulls latest .apkg from GitHub, imports it via AnkiConnect if Anki
# is running and the file changed. Triggers AnkiWeb sync after import.
#
# Runs every 30 minutes via launchd LaunchAgent (com.ezra.anki-latin.plist).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

LOG_DIR="$HOME/Library/Logs/anki-latin"
mkdir -p "$LOG_DIR" state

log() { echo "$(date -Iseconds) $*" >> "$LOG_DIR/sync.log"; }

# Pull latest
git pull --ff-only origin "$(git symbolic-ref --short HEAD)" >/dev/null 2>&1 || {
  log "git pull failed"; exit 0; }

APKG="deck/latin_iii.apkg"
[[ -f "$APKG" ]] || { log "no apkg yet"; exit 0; }

# Skip if Anki isn't running (AnkiConnect needs it open)
pgrep -x Anki >/dev/null || { log "anki not running"; exit 0; }

# Skip if .apkg unchanged since last successful import
CUR_MTIME="$(stat -f %m "$APKG")"
LAST_MTIME="$(cat state/last_import.txt 2>/dev/null || echo 0)"
if [[ "$CUR_MTIME" == "$LAST_MTIME" ]]; then
  exit 0
fi

# Call AnkiConnect importPackage
ABS_PATH="$REPO_DIR/$APKG"
RESPONSE="$(curl -fsS -X POST http://127.0.0.1:8765 -d @- <<JSON
{"action":"importPackage","version":6,"params":{"path":"$ABS_PATH"}}
JSON
)" || { log "AnkiConnect call failed"; exit 0; }

if echo "$RESPONSE" | grep -q '"error":null'; then
  echo "$CUR_MTIME" > state/last_import.txt
  log "imported ok"
  # Trigger AnkiWeb sync so phone gets it too
  curl -fsS -X POST http://127.0.0.1:8765 -d '{"action":"sync","version":6}' >/dev/null || true
  log "sync triggered"
else
  log "import error: $RESPONSE"
fi
