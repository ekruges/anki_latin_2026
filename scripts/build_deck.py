#!/usr/bin/env python3
"""
Build an Anki .apkg from a CSV with columns: Latin, Part of Speech, English, Notes.

Note GUIDs are deterministic (sha1 of normalized Latin+POS), so re-imports
update existing cards instead of duplicating them. Anki preserves review history
across re-imports as long as the GUID matches.

Usage: build_deck.py <csv_path> <apkg_out_path>
"""
from __future__ import annotations

import csv
import hashlib
import sys
import unicodedata
from pathlib import Path

import genanki

# Stable IDs. Generated once; do not change or Anki will see this as a new deck/model.
DECK_ID = 1746000001
MODEL_ID = 1746000002
DECK_NAME = "Latin III Cumulative"

CARD_CSS = """
.card {
  font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 28px;
  text-align: center;
  color: #1a1a1a;
  background: #fafafa;
  padding: 24px;
}
.latin {
  font-size: 38px;
  font-weight: 600;
  letter-spacing: 0.01em;
}
.pos {
  margin-top: 8px;
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #888;
}
hr {
  margin: 20px auto;
  width: 60%;
  border: 0;
  border-top: 1px solid #ddd;
}
.english {
  font-size: 28px;
  color: #1a1a1a;
}
.notes {
  margin-top: 18px;
  font-size: 17px;
  color: #555;
  font-style: italic;
  line-height: 1.4;
}
"""

FRONT_TMPL = """
<div class="latin">{{Latin}}</div>
{{#PartOfSpeech}}<div class="pos">{{PartOfSpeech}}</div>{{/PartOfSpeech}}
"""

BACK_TMPL = """
<div class="latin">{{Latin}}</div>
{{#PartOfSpeech}}<div class="pos">{{PartOfSpeech}}</div>{{/PartOfSpeech}}
<hr>
<div class="english">{{English}}</div>
{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}
"""

MODEL = genanki.Model(
    MODEL_ID,
    "Latin III Card",
    fields=[
        {"name": "Latin"},
        {"name": "PartOfSpeech"},
        {"name": "English"},
        {"name": "Notes"},
    ],
    templates=[
        {"name": "Latin → English", "qfmt": FRONT_TMPL, "afmt": BACK_TMPL},
    ],
    css=CARD_CSS,
)

# Map common header variants to canonical names.
HEADER_ALIASES = {
    "latin": "Latin",
    "word": "Latin",
    "term": "Latin",
    "vocabulary": "Latin",
    "vocab": "Latin",
    "part of speech": "PartOfSpeech",
    "pos": "PartOfSpeech",
    "type": "PartOfSpeech",
    "category": "PartOfSpeech",
    "english": "English",
    "definition": "English",
    "meaning": "English",
    "translation": "English",
    "notes": "Notes",
    "note": "Notes",
    "comments": "Notes",
}


def normalize_header(h: str) -> str:
    return HEADER_ALIASES.get(h.strip().lower(), h.strip())


def stable_guid(latin: str, pos: str) -> str:
    """Deterministic GUID so re-imports update rather than duplicate."""
    key = unicodedata.normalize("NFKC", f"{latin.strip().lower()}|{pos.strip().lower()}")
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def parse_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return []

    headers = [normalize_header(h) for h in rows[0]]
    notes: list[dict] = []
    for raw in rows[1:]:
        if not any(c.strip() for c in raw):
            continue
        record = {headers[i]: (raw[i].strip() if i < len(raw) else "") for i in range(len(headers))}
        latin = record.get("Latin", "").strip()
        english = record.get("English", "").strip()
        if not latin or not english:
            continue
        notes.append({
            "Latin": latin,
            "PartOfSpeech": record.get("PartOfSpeech", "").strip(),
            "English": english,
            "Notes": record.get("Notes", "").strip(),
        })
    return notes


def build(csv_path: Path, apkg_path: Path) -> int:
    records = parse_csv(csv_path)
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    for r in records:
        note = genanki.Note(
            model=MODEL,
            fields=[r["Latin"], r["PartOfSpeech"], r["English"], r["Notes"]],
            guid=stable_guid(r["Latin"], r["PartOfSpeech"]),
        )
        deck.add_note(note)
    apkg_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(apkg_path))
    return len(records)


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: build_deck.py <csv_path> <apkg_out_path>", file=sys.stderr)
        sys.exit(2)
    csv_path = Path(sys.argv[1])
    apkg_path = Path(sys.argv[2])
    count = build(csv_path, apkg_path)
    print(f"built {apkg_path} with {count} notes")


if __name__ == "__main__":
    main()
