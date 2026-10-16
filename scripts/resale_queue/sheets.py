"""Optional Google Sheets sync for the resale queue index."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .meta import INDEX_FIELDS

SHEET_HEADERS = INDEX_FIELDS


def _require_google_deps():
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Sheets sync requires optional deps. Install with: "
            "python -m pip install -r requirements-queue.txt"
        ) from exc
    return Credentials, build


def _load_credentials(credentials_path: Path):
    Credentials, _build = _require_google_deps()
    return Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )


def _read_index(root: Path) -> list[dict[str, Any]]:
    path = root / "queue-index.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run index first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("queue-index.json must be a list")
    return data


def push_index_to_sheet(
    root: Path,
    spreadsheet_id: str,
    sheet_name: str,
    credentials_path: Path,
) -> int:
    """Replace sheet body (header + rows) from queue-index.json."""
    if not spreadsheet_id.strip():
        raise ValueError("spreadsheet_id is required (flag or RESALE_SHEET_ID)")
    _, build = _require_google_deps()
    credentials = _load_credentials(credentials_path)
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    rows = _read_index(root)
    values = [SHEET_HEADERS]
    for row in rows:
        values.append([row.get(field, "") for field in SHEET_HEADERS])
    range_name = f"{sheet_name}!A1"
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:Z",
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": values},
    ).execute()
    return len(rows)


def push_from_env(root: Path) -> int:
    spreadsheet_id = os.environ.get("RESALE_SHEET_ID", "").strip()
    sheet_name = os.environ.get("RESALE_SHEET_NAME", "Queue").strip() or "Queue"
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not spreadsheet_id:
        raise ValueError("Set RESALE_SHEET_ID to the Google Spreadsheet id")
    if not credentials_path:
        raise ValueError("Set GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON path")
    return push_index_to_sheet(root, spreadsheet_id, sheet_name, Path(credentials_path))
