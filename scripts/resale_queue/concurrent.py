"""Append-only concurrency protocol for multiple chats editing one resale item.

Google Drive does not provide an atomic three-resource transaction through the
available connectors. An immutable baseline + one file per edit preserves every
acknowledged change without last-writer-wins loss. Listing/meta/Queue are merely
repairable projections of the journal, NOT concurrency-safe source documents.

No credentials, network calls, or marketplace actions are used here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from .schema import normalize_meta, validate_meta
from .reconcile import make_target

_OP_ID = re.compile(r"^[0-9a-f]{32}$")
_PATH_SEG = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")
_PROTECTED = {
    "meta.id", "meta.schema_version", "meta.sync", "meta.photos.post_count",
}


class JournalError(ValueError):
    """Invalid, incomplete or inconsistent immutable change history."""


class JournalConflict(JournalError):
    """Concurrent edits to the same field need an explicit resolution."""


@dataclass(frozen=True)
class JournalView:
    state: dict
    operation_ids: tuple[str, ...]
    revision: str
    conflicts: dict[str, dict[str, Any]]

    @property
    def can_project(self) -> bool:
        return not self.conflicts


class JournalStore(Protocol):
    """Cloud adapter must list the *entire* folder, including pagination."""

    def read_baseline(self, item_id: str) -> dict: ...
    def list_operations(self, item_id: str) -> list[dict]: ...
    def append_operation(self, item_id: str, operation: dict) -> None: ...


def _digest(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _base_state(baseline: dict) -> dict:
    if not isinstance(baseline, dict) or not isinstance(baseline.get("listing"), str):
        raise JournalError("baseline requires listing text")
    meta = validate_meta(baseline.get("meta"))
    return {"listing": baseline["listing"], "meta": meta}


def make_baseline(listing: str, meta: dict) -> dict:
    """Create once during the item migration, before opening parallel writers.

    Never silently overwrite or recreate it: multiple differing baseline files
    mean the item must be stopped and reconciled by a human.
    """
    state = _base_state({"listing": listing, "meta": meta})
    return {"format": 1, "base_hash": _digest(state), **state}


def _checked_baseline(baseline: dict) -> dict:
    if baseline.get("format") != 1:
        raise JournalError("unsupported baseline format")
    state = _base_state(baseline)
    if baseline.get("base_hash") != _digest(state):
        raise JournalError("baseline hash mismatch")
    return state


def _path(path: str) -> list[str]:
    if path == "listing":
        return ["listing"]
    if not isinstance(path, str) or not path.startswith("meta."):
        raise JournalError(f"unsupported edit path: {path!r}")
    if path in _PROTECTED or path.startswith("meta.sync."):
        raise JournalError(f"protected edit path: {path}")
    parts = path.split(".")
    if any(not _PATH_SEG.fullmatch(segment) for segment in parts):
        raise JournalError(f"invalid edit path: {path}")
    if len(parts) < 2:
        raise JournalError(f"invalid edit path: {path}")
    return parts


def _set_path(state: dict, path: str, value: Any) -> None:
    parts = _path(path)
    if path == "listing":
        if not isinstance(value, str) or not value.strip():
            raise JournalError("listing must be nonempty text")
        state["listing"] = value
        return
    cursor = state
    for segment in parts[:-1]:
        current = cursor.get(segment)
        if current is None:
            cursor[segment] = {}
        elif not isinstance(current, dict):
            raise JournalError(f"parent for {path} is not an object")
        cursor = cursor[segment]
    if isinstance(value, dict):
        raise JournalError("update scalar/array leaves, not whole objects")
    cursor[parts[-1]] = copy.deepcopy(value)


def _parse_operations(baseline: dict, operations: list[dict]) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    if not isinstance(operations, list):
        raise JournalError("journal must be a complete list")
    for raw in operations:
        if not isinstance(raw, dict):
            raise JournalError("invalid operation")
        op_id = raw.get("operation_id")
        if not isinstance(op_id, str) or not _OP_ID.fullmatch(op_id):
            raise JournalError("invalid operation ID")
        if raw.get("format") != 1 or raw.get("base_hash") != baseline["base_hash"]:
            raise JournalError(f"foreign or incompatible operation {op_id}")
        edits = raw.get("edits")
        if not isinstance(edits, dict) or not edits:
            raise JournalError("empty or invalid edit")
        for key, value in edits.items():
            _path(key)
            # Do not preserve malformed operations as immutable events.
            _set_path(copy.deepcopy({"listing": baseline["listing"], "meta": baseline["meta"]}),
                      key, value)
        # A fresh asking price or handoff is a new listing version; do not
        # accidentally reuse approval/copy tied to the previous price.
        if "meta.price.list_price_rub" in edits and (
            "listing" not in edits or "meta.price.price_selected_by_owner" not in edits
        ):
            raise JournalError("asking price requires listing and explicit owner approval update")
        if any(k in edits for k in (
            "meta.pickup_location", "meta.delivery_terms", "meta.title"
        )) and "listing" not in edits:
            raise JournalError("listing-relevant terms require updating listing text")
        if ("meta.photos.prepared_filenames" in edits
                and "meta.photos.metadata_status" not in edits):
            raise JournalError("photo list edit requires explicit sanitized metadata status")
        paths = list(edits)
        if any(
            p != q and (p.startswith(q + ".") or q.startswith(p + "."))
            for p in paths for q in paths
        ):
            raise JournalError("a change cannot edit both an object and its child")
        observed = raw.get("observed")
        if not isinstance(observed, list) or len(observed) != len(set(observed)):
            raise JournalError("invalid observed revision set")
        if any(not isinstance(x, str) or not _OP_ID.fullmatch(x) or x == op_id for x in observed):
            raise JournalError("invalid dependencies")
        # A retried create might produce another Drive file of the same name.
        # Identical operations are idempotent. Different payloads are corruption.
        if op_id in entries:
            if entries[op_id] != raw:
                raise JournalError(f"operation ID collision: {op_id}")
            continue
        entries[op_id] = copy.deepcopy(raw)
    for op in entries.values():
        if set(op["observed"]) - entries.keys():
            raise JournalError("missing parent operation; Drive listing may be incomplete")
    if any(op.get("item_id") != baseline["meta"]["id"] for op in entries.values()):
        raise JournalError("operation belongs to another item")
    return entries


def replay(baseline: dict, operations: list[dict]) -> JournalView:
    """Deterministic CRDT-like field register, with causal conflict detection.

    Disjoint paths commute. For a path, the maximal causal editors are its
    candidates. Competing concurrent values produce a visible conflict, not a
    silent winner. A new edit that observes *both* resolves it.
    """
    base = _checked_baseline(baseline)
    entries = _parse_operations(baseline, operations)
    ancestors: dict[str, set[str]] = {}

    def get_ancestors(op_id: str, visiting: set[str] | None = None) -> set[str]:
        if op_id in ancestors:
            return ancestors[op_id]
        trail = visiting or set()
        if op_id in trail:
            raise JournalError("cycle in operation dependencies")
        trail = trail | {op_id}
        result: set[str] = set()
        for previous in entries[op_id]["observed"]:
            result.add(previous)
            result.update(get_ancestors(previous, trail))
        ancestors[op_id] = result
        return result

    for op_id in entries:
        get_ancestors(op_id)

    by_path: dict[str, list[str]] = {}
    for op_id, op in entries.items():
        for path in op["edits"]:
            by_path.setdefault(path, []).append(op_id)

    # Editing a parent object and a child in different operations would make
    # conflict resolution ambiguous. Force leaf-level edits at source.
    paths = sorted(by_path)
    for index, path in enumerate(paths):
        for other in paths[index + 1:]:
            if other.startswith(path + "."):
                raise JournalError("overlapping edit paths; use leaf-level changes")

    state = copy.deepcopy(base)
    conflicts: dict[str, dict[str, Any]] = {}
    for path, writers in by_path.items():
        maximal = [
            op_id for op_id in writers
            if not any(op_id in ancestors[later] for later in writers if later != op_id)
        ]
        values = {op_id: entries[op_id]["edits"][path] for op_id in maximal}
        if len({_digest(value) for value in values.values()}) > 1:
            conflicts[path] = {k: copy.deepcopy(v) for k, v in sorted(values.items())}
            continue
        winner = values[min(values)]
        _set_path(state, path, winner)
    if "meta.photos.prepared_filenames" in by_path and not conflicts:
        state["meta"]["photos"]["post_count"] = len(state["meta"]["photos"]["prepared_filenames"])

    # Never project a conflicted state: all edits remain in the immutable log.
    if not conflicts:
        validate_meta(state["meta"])
    revision = _digest({
        "baseline": baseline["base_hash"],
        "edits": {k: entries[k] for k in sorted(entries)},
    })
    return JournalView(state=state, operation_ids=tuple(sorted(entries)),
                       revision=revision, conflicts=conflicts)


def make_operation(baseline: dict, view: JournalView, edits: dict, *,
                   operation_id: str | None = None) -> dict:
    _checked_baseline(baseline)
    if not isinstance(edits, dict) or not edits:
        raise JournalError("edits required")
    op_id = operation_id or uuid.uuid4().hex
    if not _OP_ID.fullmatch(op_id):
        raise JournalError("invalid operation ID")
    if op_id in view.operation_ids:
        raise JournalError("operation ID already used")
    for path, value in edits.items():
        _path(path)
        if isinstance(value, dict):
            raise JournalError("use leaf-level edits")
    return {
        "format": 1, "item_id": baseline["meta"]["id"],
        "operation_id": op_id, "base_hash": baseline["base_hash"],
        "observed": list(view.operation_ids),
        "edits": copy.deepcopy(edits),
    }


def append_and_verify(store: JournalStore, item_id: str, operation: dict) -> JournalView:
    """Append before touching the mutable projections, then read ALL files.

    If the upload response was lost, re-list using the same operation ID;
    never invent a second operation for the retry.
    """
    baseline = store.read_baseline(item_id)
    _checked_baseline(baseline)
    if operation.get("item_id") != item_id:
        raise JournalError("wrong item ID")
    pre = store.list_operations(item_id)
    replay(baseline, pre)  # Fail closed on missing/duplicate/corrupt history.
    # Check a prospective event before making it permanent. This may yield
    # a conflict (allowed) but must not yield invalid schema or dependencies.
    replay(baseline, [*pre, operation])
    old = {op["operation_id"]: op for op in pre}
    op_id = operation["operation_id"]
    if op_id in old:
        if old[op_id] != operation:
            raise JournalError("operation ID was reused for different content")
    else:
        try:
            store.append_operation(item_id, copy.deepcopy(operation))
        except Exception:
            # A successful upload can lose its HTTP response.
            pass
    after = store.list_operations(item_id)
    matches = [op for op in after if op.get("operation_id") == op_id]
    if not matches or any(match != operation for match in matches):
        raise JournalError("append unverified; retain same operation ID and retry listing")
    return replay(baseline, after)


def project_target(item_id: str, folder_name: str, view: JournalView):
    """Optional legacy view; safe only after a complete, conflict-free read."""
    if view.conflicts:
        raise JournalConflict(f"unresolved concurrent paths: {sorted(view.conflicts)}")
    return make_target(item_id, view.state["listing"], view.state["meta"], folder_name)
