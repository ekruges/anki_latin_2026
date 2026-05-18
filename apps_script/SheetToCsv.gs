/**
 * SheetToCsv.gs — Google Apps Script web app that returns a Google Sheet
 * as CSV over plain HTTPS. Used by the OpenClaw nightly cron to read a
 * teacher-owned sheet that we have view access to, without needing
 * third-party OAuth (which the school Workspace blocks).
 *
 * SETUP — see apps_script/README.md
 */

// Paste the teacher's sheet ID here (the long ID from the URL).
// From https://docs.google.com/spreadsheets/d/THIS_PART/edit#gid=0
const SHEET_ID = 'PASTE_TEACHER_SHEET_ID_HERE';

// Optional: pin to a specific tab name. Leave blank to use the first tab.
const TAB_NAME = '';

function doGet(e) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheet = TAB_NAME ? ss.getSheetByName(TAB_NAME) : ss.getSheets()[0];
  if (!sheet) {
    return ContentService
      .createTextOutput('error: tab not found')
      .setMimeType(ContentService.MimeType.TEXT);
  }
  const values = sheet.getDataRange().getValues();
  const csv = values.map(row => row.map(csvEscape).join(',')).join('\n');
  return ContentService
    .createTextOutput(csv)
    .setMimeType(ContentService.MimeType.TEXT);
}

function csvEscape(cell) {
  if (cell === null || cell === undefined) return '';
  let s = String(cell);
  // Dates from Sheets come through as JS Date strings; normalize whitespace.
  s = s.replace(/\r\n/g, '\n');
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    s = '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}
