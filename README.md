# anki_latin_2026

Nightly pipeline that turns the **Latin III Cumulative Vocabulary List** Google
Sheet into a clean Anki deck. Target: Latin III final on **2026-06-01**.

## Architecture

```
  Teacher-owned Google Sheet (shared with view access)
              │  read via your-identity Apps Script web app
              │  (bypasses school Workspace OAuth block)
              ▼
        OpenClaw cron @ 23:00
        ├─ curl Apps Script URL → CSV
        ├─ rebuild latin_iii.apkg (stable GUIDs)
        └─ git push if changed
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

The Apps Script deployment URL is the only sensitive bit. It lives in `.env`
on OpenClaw and is **gitignored**. No tokens, no PII in this repo. The teacher's
sheet ID is hardcoded into the script that lives on Google's servers (also
not in this repo).

## Files

- `apps_script/SheetToCsv.gs` — runs on Google's servers as you; returns sheet
  as CSV. See `apps_script/README.md` for one-time deployment.
- `scripts/build_deck.py` — CSV → `.apkg`. Stable note GUIDs so re-imports
  update cards instead of duplicating, preserving review history.
- `scripts/nightly.sh` — OpenClaw cron entrypoint.
- `mac/anki_sync.sh` — pulls + imports + AnkiWeb sync on Mac.
- `mac/com.ezra.anki-latin.plist` — LaunchAgent (every 30 min).
- `data/vocab_snapshot.csv` — last fetched CSV (committed for history).
- `deck/latin_iii.apkg` — built deck (committed).
