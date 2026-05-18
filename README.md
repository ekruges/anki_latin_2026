# anki_latin_2026

Nightly pipeline that turns the (teacher-owned, shared) **Latin III Cumulative
Vocabulary List** Google Sheet into a clean Anki deck. Target: Latin III final
on **2026-06-01**.

## Architecture

```
  Teacher-owned Google Sheet (you have view access)
              │  read via the OpenClaw schoology-sync skill's
              │  headless-Playwright cookie session
              │  (no third-party OAuth, so school admin blocks don't apply)
              ▼
        OpenClaw cron @ 23:00
        ├─ fetch_sheet.py: CSV via cookies, auto-refresh if stale
        ├─ build_deck.py:  rebuild latin_iii.apkg with stable GUIDs
        └─ git push if anything changed
              │
              ▼
         GitHub: anki_latin_2026
              │
              ▼  (Mac LaunchAgent, every 30m)
       git pull → AnkiConnect importPackage → AnkiWeb sync
              │
              ▼
         Anki (Mac + phone via AnkiWeb)
```

## Public-repo safety

- `SHEET_ID` lives in OpenClaw's gitignored `.env` (the sheet ID is mildly
  sensitive — anyone with it who also has view access could pull it).
- Cookies live in `/root/.openclaw/workspace/skills/schoology-sync/` on
  OpenClaw, never in this repo.
- No credentials, no PII anywhere in the repo.

## Files

- `scripts/fetch_sheet.py` — pulls CSV using existing schoology-sync cookies;
  calls `gdocs_auth.py` to re-auth on 401.
- `scripts/build_deck.py` — CSV → `.apkg`. Stable note GUIDs so re-imports
  update cards instead of duplicating, preserving review history. Folds any
  non-core columns (Source, Sequence, …) into the card's Notes line.
- `scripts/nightly.sh` — OpenClaw cron entrypoint.
- `mac/anki_sync.sh` — pulls + imports + AnkiWeb sync on Mac.
- `mac/com.ezra.anki-latin.plist` — LaunchAgent (every 30 min).
- `data/vocab_snapshot.csv` — last fetched CSV (committed for history).
- `deck/latin_iii.apkg` — built deck (committed).

## Restoring after a long sign-out

If you fully sign out of Google on the schoology-sync headless session,
re-auth manually:

```
ssh openclaw "cd /root/.openclaw/workspace/skills/schoology-sync && python3 scripts/gdocs_auth.py"
```

(Or just trigger any schoology-sync run; it self-heals.)
