# anki_latin_2026

Nightly pipeline that turns the **Latin III Cumulative Vocabulary List** Google
Sheet into a clean Anki deck. Target: Latin III final on **2026-06-01**.

## Architecture

```
  Google Sheet (publish-to-web CSV)
              │
              ▼
        OpenClaw cron @ 23:00
        ├─ curl CSV
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

The published-CSV URL is the only sensitive bit. It lives in `.env` on OpenClaw
and is **gitignored**. No tokens, no PII in this repo.

## Files

- `scripts/build_deck.py` — CSV → `.apkg`. Stable note GUIDs so re-imports
  update cards instead of duplicating, preserving review history.
- `scripts/nightly.sh` — OpenClaw cron entrypoint.
- `mac/anki_sync.sh` — pulls + imports + AnkiWeb sync on Mac.
- `mac/com.ezra.anki-latin.plist` — LaunchAgent (every 30 min).
- `data/vocab_snapshot.csv` — last fetched CSV (committed for history).
- `deck/latin_iii.apkg` — built deck (committed).
