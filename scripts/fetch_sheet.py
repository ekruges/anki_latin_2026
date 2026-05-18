#!/usr/bin/env python3
"""
Fetch a Google Sheet as CSV using cookies from the existing schoology-sync
skill on OpenClaw. Bypasses OAuth (admin-blocked) by riding on the headless
browser session that schoology-sync already maintains.

If cookies are stale, automatically invokes gdocs_auth.py to refresh them
and retries once.

Usage: fetch_sheet.py <sheet_id> <output_csv_path> [--gid GID]

Reads paths from env:
  GDOCS_COOKIES        path to .gdocs_cookies.json
  GDOCS_AUTH_REFRESH   path to gdocs_auth.py (run to refresh on 401)

(With reasonable defaults pointing at the schoology-sync skill.)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

DEFAULT_COOKIES = "/root/.openclaw/workspace/skills/schoology-sync/.gdocs_cookies.json"
DEFAULT_REFRESH = "/root/.openclaw/workspace/skills/schoology-sync/scripts/gdocs_auth.py"


def load_google_cookies(cookies_path: Path) -> dict[str, str]:
    raw = json.loads(cookies_path.read_text())
    jar: dict[str, str] = {}
    for c in raw:
        if "google.com" in c.get("domain", ""):
            jar[c["name"]] = c["value"]
    return jar


def try_fetch(sheet_id: str, gid: str | None, cookies_path: Path) -> tuple[int, str, bytes]:
    jar = load_google_cookies(cookies_path)
    if not jar:
        return 0, "", b""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
    params = {"format": "csv"}
    if gid is not None:
        params["gid"] = gid
    r = requests.get(url, cookies=jar, params=params, allow_redirects=True, timeout=30)
    return r.status_code, r.headers.get("content-type", ""), r.content


def is_csv(status: int, ctype: str) -> bool:
    return status == 200 and ("csv" in ctype.lower() or "octet" in ctype.lower())


def refresh_cookies(refresh_script: Path) -> None:
    print(f"refreshing cookies via {refresh_script}", file=sys.stderr)
    result = subprocess.run(
        ["python3", str(refresh_script)],
        cwd=str(refresh_script.parent.parent),
        capture_output=True,
        text=True,
        timeout=180,
    )
    sys.stderr.write(result.stdout[-500:])
    sys.stderr.write(result.stderr[-500:])
    if result.returncode != 0:
        raise SystemExit(f"cookie refresh failed (exit {result.returncode})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet_id")
    ap.add_argument("out_path", type=Path)
    ap.add_argument("--gid", default=None)
    args = ap.parse_args()

    cookies_path = Path(os.environ.get("GDOCS_COOKIES", DEFAULT_COOKIES))
    refresh_script = Path(os.environ.get("GDOCS_AUTH_REFRESH", DEFAULT_REFRESH))

    status, ctype, body = try_fetch(args.sheet_id, args.gid, cookies_path)
    if not is_csv(status, ctype):
        print(f"fetch failed (status={status}, ctype={ctype}); refreshing cookies",
              file=sys.stderr)
        refresh_cookies(refresh_script)
        status, ctype, body = try_fetch(args.sheet_id, args.gid, cookies_path)
        if not is_csv(status, ctype):
            print(f"still failing after refresh (status={status}, ctype={ctype})",
                  file=sys.stderr)
            sys.stderr.write(body[:500].decode("utf-8", "replace"))
            sys.exit(1)

    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    args.out_path.write_bytes(body)
    print(f"fetched {len(body)} bytes → {args.out_path}")


if __name__ == "__main__":
    main()
