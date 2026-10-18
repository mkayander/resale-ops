"""Optional Google Sheets sync. Never clear or replace the whole queue."""
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
            "Google Sheets sync requires optional deps. Install requirements-queue.txt"
        ) from exc
    return Credentials, build


def _load_credentials(path: Path):
    Credentials, _ = _require_google_deps()
    return Credentials.from_service_account_file(
        path, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )


def _read_index(root: Path) -> list[dict[str, Any]]:
    path = root / "queue-index.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run index first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("queue-index.json must be a list")
    ids = [row.get("id") for row in data if isinstance(row, dict)]
    if len(ids) != len(data) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("queue index contains invalid IDs or rows")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate IDs in local index")
    return data


def _header_check(values: list[list]) -> None:
    if not values:
        raise ValueError("Queue sheet has no header; initialize it before sync")
    if values[0][:len(SHEET_HEADERS)] != SHEET_HEADERS:
        raise ValueError("Queue headers differ from expected schema; refusing write")


def plan_upserts(existing: list[list], updates: list[dict]) -> list[tuple[int, list]]:
    """Pure planner. 1-based row positions; leaves unrelated rows untouched.

    Rejects duplicate existing IDs and duplicate input IDs rather than choosing
    a possibly stale row. This is not an atomic multi-client transaction.
    """
    _header_check(existing)
    seen: dict[str, int] = {}
    for row_number, row in enumerate(existing[1:], start=2):
        if not row or not str(row[0]).strip():
            continue
        key = str(row[0])
        if key in seen:
            raise ValueError(f"duplicate Queue item ID: {key}")
        seen[key] = row_number

    updates_ids: set[str] = set()
    actions: list[tuple[int, list]] = []
    next_row = max(len(existing) + 1, 2)
    for item in updates:
        key = item.get("id")
        if not isinstance(key, str) or not key:
            raise ValueError("queue upsert requires an item ID")
        if key in updates_ids:
            raise ValueError(f"duplicate update item ID: {key}")
        updates_ids.add(key)
        values = [item.get(name, "") if item.get(name) is not None else "" for name in SHEET_HEADERS]
        if key in seen:
            row = seen[key]
        else:
            row = next_row
            next_row += 1
        actions.append((row, values))
    return actions


def _quote_tab(tab: str) -> str:
    return "'" + tab.replace("'", "''") + "'"


def upsert_rows(service, spreadsheet_id: str, sheet_name: str, updates: list[dict]) -> int:
    """Update only named rows, preserving sheet extras and all other items.

    Caller must serialize concurrent writers externally. Readback detects many
    conflicts but Sheets values.update alone cannot ensure atomic compare/swap.
    """
    api = service.spreadsheets().values()
    tab = _quote_tab(sheet_name)
    last_col = "M"
    existing = api.get(
        spreadsheetId=spreadsheet_id, range=f"{tab}!A1:{last_col}",
    ).execute().get("values", [])
    actions = plan_upserts(existing, updates)
    for row_number, values in actions:
        api.update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab}!A{row_number}:{last_col}{row_number}",
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()
    verified = api.get(
        spreadsheetId=spreadsheet_id, range=f"{tab}!A1:{last_col}",
    ).execute().get("values", [])
    _header_check(verified)
    def normalized(row):
        return ["" if value is None else str(value) for value in row]

    for row_number, values in actions:
        observed = verified[row_number - 1] if row_number <= len(verified) else []
        observed = normalized(observed)
        expected = normalized(values)
        observed += [""] * max(0, len(expected) - len(observed))
        if observed[:len(expected)] != expected:
            raise RuntimeError(f"Queue readback mismatch at row {row_number}")
    final_ids = [str(row[0]) for row in verified[1:] if row and str(row[0]).strip()]
    if len(final_ids) != len(set(final_ids)):
        raise RuntimeError("concurrent change or duplicate Queue IDs after upsert")
    return len(actions)


def push_index_to_sheet(
    root: Path, spreadsheet_id: str, sheet_name: str, credentials_path: Path
) -> int:
    if not spreadsheet_id.strip():
        raise ValueError("spreadsheet_id is required")
    _, build = _require_google_deps()
    service = build(
        "sheets", "v4",
        credentials=_load_credentials(credentials_path), cache_discovery=False,
    )
    return upsert_rows(service, spreadsheet_id, sheet_name, _read_index(root))


def push_from_env(root: Path) -> int:
    spreadsheet_id = os.environ.get("RESALE_SHEET_ID", "").strip()
    sheet_name = os.environ.get("RESALE_SHEET_NAME", "Queue").strip() or "Queue"
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not spreadsheet_id or not credentials_path:
        raise ValueError("Set RESALE_SHEET_ID and GOOGLE_APPLICATION_CREDENTIALS")
    return push_index_to_sheet(root, spreadsheet_id, sheet_name, Path(credentials_path))
