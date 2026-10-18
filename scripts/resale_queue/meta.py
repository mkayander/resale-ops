"""Queue item metadata and index helpers."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .schema import normalize_meta, validate_meta, to_queue_row

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_item_id(slug: str) -> str:
    cleaned = slug.strip().lower()
    if not SLUG_RE.fullmatch(cleaned):
        raise ValueError("slug must be lowercase letters, digits, and hyphens only")
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{day}-{cleaned}"


def default_meta(item_id: str) -> dict:
    now = utc_now()
    return {
        "id": item_id,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
        "schema_version": 2,
        "title": "",
        "city": "",
        "price": {"currency": "RUB", "list_price_rub": None, "quick_sale_rub": None, "price_selected_by_owner": False},
        "platforms": {"avito": {"mode": "prepare_only", "existing_status": "unknown", "uploaded_photo_count": 0}, "youla": {"mode": "prepare_only", "existing_status": "unknown", "uploaded_photo_count": 0}},
        "photos": {
            "prepared_filenames": [],
            "post_count": 0,
            "metadata_status": "not_processed",
            "processed_at": None,
            "processor": None,
        },
        "folder_url": "",
        "pickup_location": None,
        "delivery_terms": None,
        "sheet_row": None,
        "posted": {},
        "notes": "",
    }


def init_item(root: Path, slug: str) -> Path:
    item_id = make_item_id(slug)
    item_dir = root / "queue" / item_id
    if item_dir.exists():
        raise FileExistsError(f"Item already exists: {item_dir}")
    for relative in (
        "inbox",
        "photos/post",
    ):
        (item_dir / relative).mkdir(parents=True, exist_ok=True)
    meta_path = item_dir / "meta.json"
    meta_path.write_text(
        json.dumps(default_meta(item_id), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    listing = item_dir / "listing.md"
    listing.write_text(
        f"# {item_id}\n\n"
        "<!-- Agent: fill sections from references/output.md -->\n\n"
        "## Item\n\n## Condition\n\n## Prices\n\n## Listing packages\n\n",
        encoding="utf-8",
    )
    return item_dir


def load_meta(item_dir: Path) -> dict:
    path = item_dir / "meta.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing meta.json in {item_dir}")
    return normalize_meta(json.loads(path.read_text(encoding="utf-8")))


def save_meta(item_dir: Path, meta: dict) -> None:
    """Validate, write a staging file and replace atomically on local disk."""
    safe = validate_meta(meta)
    safe["updated_at"] = utc_now()
    temp = item_dir / "meta.json.tmp"
    temp.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(item_dir / "meta.json")


INDEX_FIELDS = [
    "id",
    "status",
    "title",
    "city",
    "list_price_rub",
    "quick_sale_rub",
    "metadata_status",
    "post_photo_count",
    "prepared_at",
    "updated_at",
    "folder_name",
    "folder_url",
    "notes",
]


def build_index(root: Path) -> list[dict]:
    queue = root / "queue"
    rows: list[dict] = []
    if not queue.is_dir():
        return rows
    for item_dir in sorted(queue.iterdir()):
        if not item_dir.is_dir():
            continue
        meta_path = item_dir / "meta.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        row = to_queue_row(meta, item_dir.name)
        if row["id"] != item_dir.name:
            raise ValueError(f"folder/metadata ID mismatch for {item_dir.name}")
        rows.append(row)
    return rows


def write_index_files(root: Path, rows: list[dict]) -> tuple[Path, Path]:
    json_path = root / "queue-index.json"
    csv_path = root / "queue-index.csv"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in INDEX_FIELDS})
    return json_path, csv_path
