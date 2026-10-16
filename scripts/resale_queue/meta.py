"""Queue item metadata and index helpers."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

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
        "title": "",
        "city": "",
        "list_price_rub": None,
        "quick_sale_rub": None,
        "platforms": ["avito", "youla"],
        "photos": {
            "post": [],
            "metadata_status": "not_processed",
            "processed_at": None,
            "processor": None,
        },
        "drive_folder_url": "",
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
        "photos/original",
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
    return json.loads(path.read_text(encoding="utf-8"))


def save_meta(item_dir: Path, meta: dict) -> None:
    meta["updated_at"] = utc_now()
    (item_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
    "drive_folder_url",
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
        photos = meta.get("photos") or {}
        post = photos.get("post") or []
        rows.append(
            {
                "id": meta.get("id", item_dir.name),
                "status": meta.get("status", "draft"),
                "title": meta.get("title", ""),
                "city": meta.get("city", ""),
                "list_price_rub": meta.get("list_price_rub"),
                "quick_sale_rub": meta.get("quick_sale_rub"),
                "metadata_status": photos.get("metadata_status", ""),
                "post_photo_count": len(post),
                "prepared_at": photos.get("processed_at") or meta.get("created_at"),
                "updated_at": meta.get("updated_at", ""),
                "folder_name": item_dir.name,
                "drive_folder_url": meta.get("drive_folder_url", ""),
                "notes": meta.get("notes", ""),
            }
        )
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
