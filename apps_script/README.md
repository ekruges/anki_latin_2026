# Apps Script web app — sheet → CSV

Why this exists: school Workspace blocks third-party OAuth (rclone, gspread,
etc.), and the teacher owns the sheet so we can't `File → Publish to web`.
This Apps Script runs **inside Google as your identity**, returns the sheet
as CSV over a plain HTTPS URL. Cron just `curl`s it.

## One-time setup

1. Open the teacher's "Latin III Cumulative Vocabulary List" sheet in your
   browser. From the URL, copy the long ID between `/d/` and `/edit`:
   ```
   https://docs.google.com/spreadsheets/d/[THIS_PART]/edit#gid=0
   ```

2. Go to **https://script.google.com/** → **New project**.

3. Delete the default `function myFunction()` boilerplate. Paste the entire
   contents of [`SheetToCsv.gs`](./SheetToCsv.gs).

4. Replace `PASTE_TEACHER_SHEET_ID_HERE` with the ID from step 1. If the vocab
   is on a non-first tab, also fill in `TAB_NAME`.

5. Save (`⌘S`). Give the project a name like `latin-iii-csv-feed`.

6. **Deploy → New deployment**:
   - Type: **Web app**
   - Description: anything
   - Execute as: **Me (you@cgps.org)**
   - Who has access: **Anyone with the link** *(safe — URL is unguessable)*
   - Click **Deploy**

7. First-time auth prompt: click **Authorize access** → pick your school
   account → scary "Google hasn't verified this app" screen → **Advanced** →
   "Go to latin-iii-csv-feed (unsafe)" → **Allow**. This is your own script
   asking for permission to read sheets on your behalf — fine.

8. Copy the **Web app URL** (`https://script.google.com/macros/s/AKfycb.../exec`).
   Send it to me; I'll drop it into OpenClaw's gitignored `.env`.

## When the teacher updates the sheet

Nothing to do. The Apps Script reads live each time the URL is hit. Cron pulls
nightly at 23:00, but you can hit the URL in a browser any time to see exactly
what the cron will see.

## Updating the script later

If you change `SheetToCsv.gs`, you must **Deploy → Manage deployments →
pencil icon → Version: New version → Deploy** for the change to take effect.
The URL stays the same.

## If admin still blocks Apps Script deployment

Rare but possible. Symptom: step 6 errors out with "Your administrator has
disabled this". Fallback: deploy from your personal `kruger.ezra.s@gmail.com`
account, but then you need the teacher to share the sheet with that email too.
