#!/usr/bin/env bash
# Nightly job (runs on OpenClaw): fetch CSV, rebuild .apkg, commit if changed.
#
# Requires:
#   - .env in repo root with CSV_URL=...
#   - python3 + genanki installed (pip install --user genanki)
#   - SSH access to GitHub for git push (deploy key or agent forwarding)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# Load CSV_URL
if [[ ! -f .env ]]; then
  echo "missing .env (copy from .env.example)" >&2
  exit 1
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

if [[ -z "${CSV_URL:-}" || "$CSV_URL" == *REPLACE-ME* ]]; then
  echo "CSV_URL not set in .env" >&2
  exit 1
fi

mkdir -p data deck state

# Sync with remote first (in case of conflicts)
git pull --rebase --autostash origin "$(git symbolic-ref --short HEAD)" >/dev/null 2>&1 || true

# Fetch CSV
TMP_CSV="$(mktemp)"
trap 'rm -f "$TMP_CSV"' EXIT
curl -fsSL "$CSV_URL" -o "$TMP_CSV"

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
