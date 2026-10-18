"""Canonical metadata schema and non-destructive legacy reader.

Version 2 matches the cloud queue. Older local flat metadata remains readable;
normalization never writes changes back without an explicit save.
"""
from __future__ import annotations

import copy
import re
from pathlib import PurePosixPath

SCHEMA_VERSION = 2
STATUSES = {"draft", "researching", "ready", "posted", "published", "sold", "archived"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
POST_NAME = re.compile(r"^\d{2,}(?:[_-][^/\\]+)?\.jpe?g$", re.IGNORECASE)


def normalize_meta(raw: dict) -> dict:
    """Return a canonical copy, preserving user-specific/unknown fields."""
    if not isinstance(raw, dict):
        raise ValueError("meta.json must be an object")
    version = raw.get("schema_version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or not 1 <= version <= SCHEMA_VERSION:
        raise ValueError("unsupported metadata schema version")
    meta = copy.deepcopy(raw)
    meta["schema_version"] = SCHEMA_VERSION
    price = meta.setdefault("price", {})
    if not isinstance(price, dict):
        raise ValueError("price must be an object")
    for field in ("list_price_rub", "quick_sale_rub"):
        if field not in price and field in meta:
            price[field] = meta.pop(field)
        elif field in price and field in meta:
            if price[field] != meta[field]:
                raise ValueError(f"conflicting flat and nested {field}")
            meta.pop(field, None)
    price.setdefault("currency", "RUB")
    price.setdefault("price_selected_by_owner", False)

    photos = meta.setdefault("photos", {})
    if not isinstance(photos, dict):
        raise ValueError("photos must be an object")
    if "prepared_filenames" not in photos:
        photos["prepared_filenames"] = [
            PurePosixPath(path).name for path in photos.get("post", [])
        ]
    if "post" in photos and "prepared_filenames" in raw.get("photos", {}):
        legacy = [PurePosixPath(path).name for path in photos["post"]]
        if legacy != photos["prepared_filenames"]:
            raise ValueError("conflicting old and new posting photo lists")
    photos.pop("post", None)
    count = len(photos["prepared_filenames"])
    if "post_count" in photos and photos["post_count"] != count:
        raise ValueError("post_count conflicts with prepared_filenames")
    photos["post_count"] = count
    photos.setdefault("metadata_status", "not_processed")

    platforms = meta.setdefault("platforms", {})
    if isinstance(platforms, list):
        meta["platforms"] = {
            name: {"mode": "prepare_only", "existing_status": "unknown",
                   "posted_url": None, "uploaded_photo_count": 0}
            for name in platforms
        }
    elif not isinstance(platforms, dict):
        raise ValueError("platforms must be an object")
    meta.setdefault("status", "draft")
    return meta


def validate_meta(raw: dict, *, ready_check: bool = True) -> dict:
    """Validate core invariants; return normalized data without mutating input."""
    meta = normalize_meta(raw)
    item_id = meta.get("id")
    if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id):
        raise ValueError("invalid item id")
    if meta.get("status") not in STATUSES:
        raise ValueError("invalid item status")
    for field in ("title", "city"):
        if meta.get(field) is not None and not isinstance(meta[field], str):
            raise ValueError(f"{field} must be a string")
    price = meta["price"]
    for field in ("list_price_rub", "quick_sale_rub"):
        v = price.get(field)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0):
            raise ValueError(f"invalid {field}")
    filenames = meta["photos"]["prepared_filenames"]
    if not isinstance(filenames, list) or any(
        not isinstance(name, str) or not POST_NAME.fullmatch(name)
        for name in filenames
    ):
        raise ValueError("invalid prepared photo filenames")
    if len(filenames) != len(set(filenames)):
        raise ValueError("duplicate prepared photo filenames")
    if not isinstance(meta["platforms"], dict):
        raise ValueError("invalid platforms")
    sync = meta.get("sync")
    if sync is not None:
        if not isinstance(sync, dict):
            raise ValueError("sync must be an object")
        digest = sync.get("listing_sha256")
        if digest is not None and (
            not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError("invalid listing_sha256")
    if ready_check and meta["status"] == "ready":
        if not meta.get("title") or not meta.get("city"):
            raise ValueError("ready requires title and city")
        if price.get("list_price_rub") is None or not price.get("price_selected_by_owner"):
            raise ValueError("ready requires an owner-approved asking price")
        if not filenames or meta["photos"].get("metadata_status") != "stripped_verified":
            raise ValueError("ready requires sanitized posting photos")
        if not meta.get("pickup_location") and not meta.get("delivery_terms"):
            raise ValueError("ready requires agreed handoff terms")
    return meta


def to_queue_row(raw: dict, folder_name: str) -> dict:
    meta = validate_meta(raw)
    photo = meta["photos"]
    price = meta["price"]
    return {
        "id": meta["id"],
        "status": meta["status"],
        "title": meta.get("title") or "",
        "city": meta.get("city") or "",
        "list_price_rub": price.get("list_price_rub") or "",
        "quick_sale_rub": price.get("quick_sale_rub") or "",
        "metadata_status": photo.get("metadata_status", ""),
        "post_photo_count": len(photo["prepared_filenames"]),
        "prepared_at": meta.get("prepared_at") or photo.get("processed_at") or meta.get("created_at") or "",
        "updated_at": meta.get("updated_at") or "",
        "folder_name": folder_name,
        "folder_url": meta.get("folder_url") or meta.get("drive_folder_url") or "",
        "notes": meta.get("notes") or "",
    }
