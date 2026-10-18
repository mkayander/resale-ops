"""Idempotent, conflict-aware reconciliation of a *single* resale item.

Adapters provide read/write operations for existing Drive files and an ID-based
Queue upsert. This module intentionally has no Google dependency or credentials.
It never creates files, retries a marketplace action or modifies another item.
"""
from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Protocol

from .meta import INDEX_FIELDS
from .schema import normalize_meta, to_queue_row, validate_meta


@dataclass(frozen=True)
class Snapshot:
    listing: str
    meta: dict
    queue: dict | None


@dataclass(frozen=True)
class Target:
    listing: str
    meta: dict
    queue: dict


@dataclass(frozen=True)
class ReconcileResult:
    changed: tuple[str, ...]
    unchanged: tuple[str, ...]


class ItemStore(Protocol):
    """Implement with stable existing Drive file IDs and Queue row item ID."""

    def read_listing(self, item_id: str) -> str: ...
    def write_listing(self, item_id: str, text: str) -> None: ...
    def read_meta(self, item_id: str) -> dict: ...
    def write_meta(self, item_id: str, meta: dict) -> None: ...
    def read_queue(self, item_id: str) -> dict | None: ...
    def upsert_queue(self, item_id: str, row: dict) -> None: ...


class ReconcileConflict(RuntimeError):
    """Somebody changed the persisted resource since the initial snapshot."""


class ReconcileFailure(RuntimeError):
    def __init__(self, resource: str, completed: tuple[str, ...], reason: str):
        super().__init__(f"{resource}: {reason}; verified before failure: {completed}")
        self.resource = resource
        self.completed = completed


def listing_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def make_target(item_id: str, listing: str, raw_meta: dict, folder_name: str) -> Target:
    """Generate exact persistent values from one approved listing revision."""
    if not isinstance(listing, str) or not listing.strip():
        raise ValueError("listing.md must contain approved listing text")
    meta = validate_meta(raw_meta)
    if meta["id"] != item_id or item_id != folder_name:
        raise ValueError("stable item ID and folder name must match")
    meta.setdefault("sync", {})
    if not isinstance(meta["sync"], dict):
        raise ValueError("sync must be an object")
    meta["sync"]["listing_sha256"] = listing_digest(listing)
    row = to_queue_row(meta, folder_name)
    return Target(listing=listing, meta=meta, queue=row)


def snapshot(store: ItemStore, item_id: str) -> Snapshot:
    """Read all three resources; do not mutate anything."""
    listing = store.read_listing(item_id)
    raw_meta = store.read_meta(item_id)
    if not isinstance(raw_meta, dict) or raw_meta.get("id") != item_id:
        raise ValueError("wrong item ID returned from metadata store")
    queue = store.read_queue(item_id)
    if queue is not None and queue.get("id") != item_id:
        raise ValueError("wrong item ID returned from Queue")
    return Snapshot(listing=listing, meta=raw_meta, queue=queue)


def _equal_meta(a: dict, b: dict) -> bool:
    return normalize_meta(a) == normalize_meta(b)


def _equal_queue(a: dict | None, b: dict | None) -> bool:
    if a is None or b is None:
        return a is b
    # Google Sheets may render numeric values as 2900 or 2900.0.
    # All managed fields must agree; extra columns are outside our ownership.
    return all(
        str(a.get(field, "") if a.get(field) is not None else "") ==
        str(b.get(field, "") if b.get(field) is not None else "")
        for field in INDEX_FIELDS
    )


def _equal_listing(a: str, b: str) -> bool:
    return a == b


def reconcile(store: ItemStore, item_id: str, before: Snapshot, target: Target) -> ReconcileResult:
    """Resume the same requested change safely after partial write failures.

    Must reuse *the original* before + target on retry. A current value equal to
    target is already complete. A current value equal to before can be updated.
    Any third value is a conflict, never silently overwritten.

    Writes are ordered listing -> meta -> Queue. Each write is read back. If
    the writer raises after actually committing, readback still recognizes it.
    There is deliberately no automatic rollback of already-verified writes:
    re-running this function with the same arguments converges safely.
    """
    if not isinstance(before, Snapshot) or not isinstance(target, Target):
        raise TypeError("snapshot and target are required")
    verified_meta = validate_meta(target.meta)
    if (item_id != verified_meta["id"] or target.queue.get("id") != item_id
            or verified_meta.get("sync", {}).get("listing_sha256") != listing_digest(target.listing)):
        raise ValueError("target ID or listing digest mismatch")
    if not _equal_queue(target.queue, to_queue_row(verified_meta, item_id)):
        raise ValueError("target Queue row is inconsistent with metadata")

    completed: list[str] = []
    skipped: list[str] = []
    steps = (
        ("listing.md", lambda: store.read_listing(item_id), before.listing,
         target.listing, lambda v: store.write_listing(item_id, v), _equal_listing),
        ("meta.json", lambda: store.read_meta(item_id), before.meta,
         target.meta, lambda v: store.write_meta(item_id, copy.deepcopy(v)), _equal_meta),
        ("Queue", lambda: store.read_queue(item_id), before.queue,
         target.queue, lambda v: store.upsert_queue(item_id, copy.deepcopy(v)), _equal_queue),
    )
    for label, read, previous, expected, write, equal in steps:
        try:
            actual = read()
        except Exception as exc:
            raise ReconcileFailure(label, tuple(completed), "read failed") from exc
        if equal(actual, expected):
            skipped.append(label)
            continue
        if not equal(actual, previous):
            raise ReconcileConflict(f"{label}: external change detected; no write performed")
        try:
            write(expected)
        except Exception as exc:
            # Some APIs may commit and then return an ambiguous error.
            # Read back once to distinguish that case; don't blindly retry.
            try:
                if equal(read(), expected):
                    completed.append(label)
                    continue
            except Exception:
                pass
            raise ReconcileFailure(label, tuple(completed), "write failed or result unknown") from exc
        try:
            if not equal(read(), expected):
                raise ReconcileFailure(label, tuple(completed), "readback mismatch")
        except ReconcileFailure:
            raise
        except Exception as exc:
            raise ReconcileFailure(label, tuple(completed), "readback failed") from exc
        completed.append(label)
    return ReconcileResult(tuple(completed), tuple(skipped))
