from __future__ import annotations

from typing import Any

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def export_rows(
    credentials_json_path: str,
    spreadsheet_id: str,
    worksheet_title: str,
    rows: list[dict[str, Any]],
) -> None:
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is empty.")

    creds = Credentials.from_service_account_file(credentials_json_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)

    try:
        ws = sh.worksheet(worksheet_title)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_title, rows=1200, cols=12)

    header = ["rank", "symbol", "sctr", "perf_1d", "perf_5d", "perf_20d", "perf_60d", "rsi_14"]
    body = [[r.get(k) for k in header] for r in rows]
    ws.update([header, *body], value_input_option="RAW")
