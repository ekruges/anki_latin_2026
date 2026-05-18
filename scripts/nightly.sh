#!/usr/bin/env bash
# Nightly job (runs on OpenClaw): fetch sheet → rebuild .apkg → commit if changed.
#
# Requires:
#   - .env in repo root with SHEET_ID (and optionally SHEET_GID)
#   - python3 + genanki + requests
#   - The schoology-sync skill at the default path (for Google cookies +
#     headless re-auth on stale sessions). Override via GDOCS_* env vars.
#   - SSH deploy key for git push
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "missing .env (copy from .env.example)" >&2
  exit 1
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

if [[ -z "${SHEET_ID:-}" || "$SHEET_ID" == *REPLACE-ME* ]]; then
  echo "SHEET_ID not set in .env" >&2
  exit 1
fi

mkdir -p data deck state

# Sync with remote first (in case of conflicts)
git pull --rebase --autostash origin "$(git symbolic-ref --short HEAD)" >/dev/null 2>&1 || true

# Fetch CSV via existing schoology-sync cookies
TMP_CSV="$(mktemp)"
trap 'rm -f "$TMP_CSV"' EXIT
GID_ARG=()
[[ -n "${SHEET_GID:-}" ]] && GID_ARG=(--gid "$SHEET_GID")
python3 scripts/fetch_sheet.py "$SHEET_ID" "$TMP_CSV" "${GID_ARG[@]}"

# Hash check: only rebuild + commit when the upstream sheet actually changed
NEW_SHA="$(sha256sum "$TMP_CSV" | cut -d' ' -f1)"
OLD_SHA="$(cat state/last_csv_sha.txt 2>/dev/null || true)"

if [[ "$NEW_SHA" == "$OLD_SHA" ]]; then
  echo "$(date -Iseconds) no change (sha=$NEW_SHA)"
  exit 0
fi

mv "$TMP_CSV" data/vocab_snapshot.csv
trap - EXIT

python3 scripts/build_deck.py data/vocab_snapshot.csv deck/latin_iii.apkg

echo "$NEW_SHA" > state/last_csv_sha.txt

git add data/vocab_snapshot.csv deck/latin_iii.apkg
if git diff --cached --quiet; then
  echo "$(date -Iseconds) csv changed but no diff in tracked files"
  exit 0
fi

git -c user.name="OpenClaw Nightly" -c user.email="openclaw@ekruger.local" \
  commit -m "nightly: refresh Latin III deck ($(date -u +%Y-%m-%d))"
git push origin "$(git symbolic-ref --short HEAD)"
echo "$(date -Iseconds) pushed update"
