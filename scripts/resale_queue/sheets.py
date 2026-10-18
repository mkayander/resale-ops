"""Optional Google Sheets sync. Never clear or replace the whole queue."""
from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation
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
    a possibly stale row. Partial updates retain existing unspecified fields.
    This is not an atomic multi-client transaction.
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
        if key in seen:
            row = seen[key]
            # Preserve existing values in columns omitted by a partial patch.
            # An explicit None/empty string is a deliberate request to clear.
            values = list(existing[row - 1][:len(SHEET_HEADERS)])
            values += [""] * (len(SHEET_HEADERS) - len(values))
        else:
            row = next_row
            next_row += 1
            values = [""] * len(SHEET_HEADERS)
        for column, name in enumerate(SHEET_HEADERS):
            if name in item:
                values[column] = item[name] if item[name] is not None else ""
        actions.append((row, values))
    return actions


def _quote_tab(tab: str) -> str:
    return "'" + tab.replace("'", "''") + "'"


class QueueConflict(RuntimeError):
    """Queue changed during a write; caller must inspect before retrying."""


_NUMERIC_COLUMNS = {"list_price_rub", "quick_sale_rub", "post_photo_count"}


def _cell_equal(column: int, observed: object, expected: object) -> bool:
    if observed is None or observed == "":
        observed = ""
    if expected is None or expected == "":
        expected = ""
    if SHEET_HEADERS[column] in _NUMERIC_COLUMNS:
        try:
            return Decimal(str(observed)) == Decimal(str(expected))
        except InvalidOperation:
            pass
    return str(observed) == str(expected)


def _lookup(rows: list[list], item_id: str) -> tuple[int | None, list]:
    """Locate the item from a FRESH sheet read; detect all duplicate IDs."""
    _header_check(rows)
    found = []
    seen = set()
    for row_no, row in enumerate(rows[1:], 2):
        if not row or not str(row[0]).strip():
            continue
        key = str(row[0])
        if key in seen:
            raise QueueConflict(f"duplicate Queue item ID: {key}")
        seen.add(key)
        if key == item_id:
            found.append((row_no, row))
    return found[0] if found else (None, [])


def _read_rows(api, spreadsheet_id: str, tab: str) -> list[list]:
    return api.get(
        spreadsheetId=spreadsheet_id,
        range=f"{tab}!A1:M",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute().get("values", [])


def _column_a1(index: int) -> str:
    return chr(ord("A") + index)


def upsert_rows(service, spreadsheet_id: str, sheet_name: str, updates: list[dict]) -> int:
    """Upsert separate items without cached row numbers or computed append slots.

    New items use server-positioned values.append(INSERT_ROWS); existing items
    patch only specified cells. Every item is re-located by its ID and read
    back after writing, so other chats can append, reorder or edit other items.

    This cannot provide atomic compare-and-swap: a physical row deletion in the
    few milliseconds between the ID check and a positional batchUpdate can
    still move the target. Prefer soft deletion/archiving while chats write.
    """
    ids: set[str] = set()
    for patch in updates:
        item_id = patch.get("id") if isinstance(patch, dict) else None
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("queue upsert requires an item ID")
        if item_id in ids:
            raise ValueError(f"duplicate update item ID: {item_id}")
        unknown = set(patch) - set(SHEET_HEADERS)
        if unknown:
            raise ValueError(f"unknown Queue columns: {sorted(unknown)}")
        ids.add(item_id)

    api = service.spreadsheets().values()
    tab = _quote_tab(sheet_name)
    for patch in updates:
        item_id = patch["id"]
        # Do not cache sheet row indices across operations. Physical row
        # insert/delete can shift EVERY row below it.
        existing = _read_rows(api, spreadsheet_id, tab)
        row_no, row = _lookup(existing, item_id)
        if row_no is None:
            values = [patch.get(name, "") if patch.get(name) is not None else ""
                      for name in SHEET_HEADERS]
            # The server locates the current end of the logical table, instead
            # of trusting len(existing)+1 from an earlier snapshot.
            try:
                api.append(
                    spreadsheetId=spreadsheet_id,
                    range=f"{tab}!A:M",
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [values]},
                ).execute()
            except Exception as exc:
                # An ambiguous response can still mean the row was appended;
                # inspect first, never immediately repeat the append.
                check_no, check_row = _lookup(_read_rows(api, spreadsheet_id, tab), item_id)
                if check_no is None or any(
                    not _cell_equal(i, check_row[i] if i < len(check_row) else "", val)
                    for i, val in enumerate(values)
                ):
                    raise QueueConflict(f"append for {item_id} failed or is unverified") from exc
        else:
            # A cheap final identity check catches rows shifted after the
            # initial lookup (e.g. manual deletion/insert in a second chat).
            identity = api.get(
                spreadsheetId=spreadsheet_id,
                range=f"{tab}!A{row_no}",
                valueRenderOption="UNFORMATTED_VALUE",
            ).execute().get("values", [])
            if not identity or not identity[0] or str(identity[0][0]) != item_id:
                raise QueueConflict(f"row for {item_id} moved; retry after refresh")
            # Patch just the supplied cells: do not overwrite an unrelated
            # update of another column or any formula in an untouched column.
            data = []
            for i, name in enumerate(SHEET_HEADERS[1:], start=1):
                if name not in patch:
                    continue
                value = patch[name] if patch[name] is not None else ""
                current = row[i] if i < len(row) else ""
                if not _cell_equal(i, current, value):
                    data.append({
                        "range": f"{tab}!{_column_a1(i)}{row_no}",
                        "values": [[value]],
                    })
            if data:
                try:
                    api.batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body={"valueInputOption": "RAW", "data": data},
                    ).execute()
                except Exception as exc:
                    # A failed API response does not authorize blind retries.
                    raise QueueConflict(f"update for {item_id} failed or is unverified") from exc

        checked = _read_rows(api, spreadsheet_id, tab)
        actual_no, actual_row = _lookup(checked, item_id)
        if actual_no is None:
            raise QueueConflict(f"item {item_id} vanished after writing")
        for i, name in enumerate(SHEET_HEADERS):
            if name not in patch:
                continue
            observed = actual_row[i] if i < len(actual_row) else ""
            expected = patch[name] if patch[name] is not None else ""
            if not _cell_equal(i, observed, expected):
                raise QueueConflict(f"Queue readback mismatch: item={item_id}, column={name}")
    return len(updates)


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
