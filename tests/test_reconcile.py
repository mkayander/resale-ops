"""Offline recovery tests for existing Drive file IDs and Queue row by ID."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.reconcile import (
    ReconcileConflict, ReconcileFailure, make_target, reconcile, snapshot,
)


class FakeStore:
    def __init__(self, item_id="test-cooler"):
        self.item_id = item_id
        self.listing = "Old draft"
        self.meta = {"id": item_id, "status": "draft", "title": "Cooler",
                     "city": "Москва", "price": {"list_price_rub": 3000},
                     "photos": {"prepared_filenames": [], "metadata_status": "not_processed"}}
        self.queue = None
        self.writes = []
        self.fail = None
        self.commit_before_error = False

    def read_listing(self, item_id):
        assert item_id == self.item_id
        return self.listing

    def write_listing(self, item_id, text):
        self._write("listing", lambda: setattr(self, "listing", text))

    def read_meta(self, item_id):
        assert item_id == self.item_id
        return copy.deepcopy(self.meta)

    def write_meta(self, item_id, data):
        self._write("meta", lambda: setattr(self, "meta", copy.deepcopy(data)))

    def read_queue(self, item_id):
        assert item_id == self.item_id
        return copy.deepcopy(self.queue)

    def upsert_queue(self, item_id, row):
        assert item_id == self.item_id
        self._write("queue", lambda: setattr(self, "queue", copy.deepcopy(row)))

    def _write(self, name, mutation):
        self.writes.append(name)
        if self.fail == name and not self.commit_before_error:
            raise ConnectionError(f"{name} unavailable")
        mutation()
        if self.fail == name and self.commit_before_error:
            raise ConnectionError(f"{name} committed, but response lost")


def ready_target(store):
    meta = store.read_meta(store.item_id)
    meta.update({
        "status": "ready",
        "pickup_location": "Москва, метро Севастопольская",
        "price": {"list_price_rub": 2900, "quick_sale_rub": 1900,
                  "price_selected_by_owner": True},
        "photos": {"prepared_filenames": ["01.jpg"], "metadata_status": "stripped_verified"},
    })
    return make_target(store.item_id, "Cooler, 2900 ₽; самовывоз Севастопольская", meta, store.item_id)


class ReconciliationTest(unittest.TestCase):
    def test_fully_idempotent_write_and_readback(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        first = reconcile(store, store.item_id, prior, target)
        self.assertEqual(first.changed, ("listing.md", "meta.json", "Queue"))
        self.assertEqual(store.meta["sync"]["listing_sha256"], target.meta["sync"]["listing_sha256"])
        repeated = reconcile(store, store.item_id, prior, target)
        self.assertFalse(repeated.changed)
        self.assertEqual(repeated.unchanged, ("listing.md", "meta.json", "Queue"))
        self.assertEqual(store.writes, ["listing", "meta", "queue"])

    def test_failed_queue_write_recovers_without_touching_completed_drive_files(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        store.fail = "queue"
        with self.assertRaises(ReconcileFailure) as caught:
            reconcile(store, store.item_id, prior, target)
        self.assertEqual(caught.exception.resource, "Queue")
        self.assertEqual(caught.exception.completed, ("listing.md", "meta.json"))
        store.fail = None
        resumed = reconcile(store, store.item_id, prior, target)
        self.assertEqual(resumed.changed, ("Queue",))
        self.assertEqual(resumed.unchanged, ("listing.md", "meta.json"))
        self.assertEqual(store.queue["list_price_rub"], 2900)

    def test_lost_response_after_commit_does_not_repeat_operation(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        store.fail = "meta"
        store.commit_before_error = True
        result = reconcile(store, store.item_id, prior, target)
        self.assertEqual(result.changed, ("listing.md", "meta.json", "Queue"))
        self.assertEqual(store.writes.count("meta"), 1)

    def test_external_edit_causes_conflict_without_overwrite(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        store.listing = "Another editor changed this listing"
        with self.assertRaises(ReconcileConflict):
            reconcile(store, store.item_id, prior, target)
        self.assertEqual(store.writes, [])
        self.assertEqual(store.listing, "Another editor changed this listing")

    def test_midflight_queue_change_is_not_overwritten(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        store.queue = {"id": store.item_id, "status": "published"}
        with self.assertRaises(ReconcileConflict):
            reconcile(store, store.item_id, prior, target)
        self.assertEqual(store.queue["status"], "published")
        self.assertEqual(store.writes, ["listing", "meta"])

    def test_target_digest_does_not_permit_stale_listing(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        target.meta["sync"]["listing_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "digest"):
            reconcile(store, store.item_id, prior, target)
        self.assertFalse(store.writes)

    def test_invalid_ready_target_has_no_side_effects(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        meta = store.read_meta(store.item_id)
        meta["status"] = "ready"
        with self.assertRaisesRegex(ValueError, "owner-approved"):
            make_target(store.item_id, "Cooler", meta, store.item_id)
        self.assertEqual(store.listing, prior.listing)
        self.assertIsNone(store.queue)

    def test_wrong_item_from_store_stops_read(self):
        store = FakeStore()
        store.meta["id"] = "other-item"
        with self.assertRaisesRegex(ValueError, "wrong item ID"):
            snapshot(store, store.item_id)

    def test_empty_queue_patch_preserves_unrelated_item(self):
        store = FakeStore()
        prior = snapshot(store, store.item_id)
        target = ready_target(store)
        reconcile(store, store.item_id, prior, target)
        self.assertEqual(store.queue["id"], store.item_id)


if __name__ == "__main__":
    unittest.main()
