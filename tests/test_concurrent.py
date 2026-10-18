"""Synthetic concurrent-chat tests. Every operation is immutable/offline."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.concurrent import (
    JournalConflict, JournalError, append_and_verify, make_baseline,
    make_operation, project_target, replay,
)


def base():
    return make_baseline(
        "# Cooler\nAsking price 2900 ₽. Pickup in Moscow.",
        {"id": "test-cooler", "title": "Cooler", "city": "Москва",
         "status": "ready", "pickup_location": "Москва",
         "price": {"list_price_rub": 2900, "quick_sale_rub": 1900,
                   "price_selected_by_owner": True},
         "photos": {"prepared_filenames": ["01.jpg"],
                    "metadata_status": "stripped_verified"}},
    )


class FakeJournal:
    def __init__(self, baseline):
        self.baseline = copy.deepcopy(baseline)
        self.ops = []
        self.fail_after_commit = False
        self.fail_before_commit = False

    def read_baseline(self, item_id):
        assert item_id == "test-cooler"
        return copy.deepcopy(self.baseline)

    def list_operations(self, item_id):
        assert item_id == "test-cooler"
        return copy.deepcopy(self.ops)

    def append_operation(self, item_id, operation):
        assert item_id == "test-cooler"
        if self.fail_before_commit:
            raise ConnectionError("Google unavailable before write")
        self.ops.append(copy.deepcopy(operation))
        if self.fail_after_commit:
            raise ConnectionError("Google response lost")


def edit(baseline, view, updates, index):
    return make_operation(baseline, view, updates, operation_id=f"{index:032x}")


class ConcurrentChatTest(unittest.TestCase):
    def test_disjoint_changes_from_two_stale_chats_merge(self):
        baseline = base()
        first_read = replay(baseline, [])
        a = edit(baseline, first_read, {"meta.notes": "Includes ice packs"}, 1)
        b = edit(baseline, first_read, {"meta.price.quick_sale_rub": 1750}, 2)
        merged = replay(baseline, [b, a])
        self.assertFalse(merged.conflicts)
        self.assertEqual(merged.state["meta"]["notes"], "Includes ice packs")
        self.assertEqual(merged.state["meta"]["price"]["quick_sale_rub"], 1750)
        self.assertEqual(merged.revision, replay(baseline, [a, b]).revision)
        project = project_target("test-cooler", "test-cooler", merged)
        self.assertEqual(project.queue["list_price_rub"], 2900)

    def test_same_price_concurrent_proposals_block_projection(self):
        baseline = base()
        before = replay(baseline, [])
        a = edit(baseline, before, {"meta.price.quick_sale_rub": 1800}, 1)
        b = edit(baseline, before, {"meta.price.quick_sale_rub": 1500}, 2)
        merged = replay(baseline, [a, b])
        self.assertIn("meta.price.quick_sale_rub", merged.conflicts)
        self.assertEqual(len(merged.conflicts["meta.price.quick_sale_rub"]), 2)
        with self.assertRaises(JournalConflict):
            project_target("test-cooler", "test-cooler", merged)

        # A third chat sees both proposals and deliberately picks a resolution.
        resolved = edit(baseline, merged, {"meta.price.quick_sale_rub": 1700}, 3)
        final = replay(baseline, [a, b, resolved])
        self.assertFalse(final.conflicts)
        self.assertEqual(final.state["meta"]["price"]["quick_sale_rub"], 1700)

    def test_concurrent_identical_value_is_not_conflict(self):
        baseline = base()
        before = replay(baseline, [])
        a = edit(baseline, before, {"meta.notes": "Ice packs"}, 1)
        b = edit(baseline, before, {"meta.notes": "Ice packs"}, 2)
        merged = replay(baseline, [b, a])
        self.assertFalse(merged.conflicts)
        self.assertEqual(merged.state["meta"]["notes"], "Ice packs")

    def test_causal_overwrite_is_not_conflict(self):
        baseline = base()
        before = replay(baseline, [])
        a = edit(baseline, before, {"meta.notes": "Earlier note"}, 1)
        later = edit(baseline, replay(baseline, [a]), {"meta.notes": "Later note"}, 2)
        self.assertEqual(
            replay(baseline, [later, a]).state["meta"]["notes"], "Later note"
        )

    def test_partial_google_failure_preserves_journal(self):
        baseline = base()
        store = FakeJournal(baseline)
        op = edit(baseline, replay(baseline, []), {"meta.notes": "One"}, 1)
        store.fail_after_commit = True
        result = append_and_verify(store, "test-cooler", op)
        self.assertEqual(result.state["meta"]["notes"], "One")
        self.assertEqual(len(store.ops), 1)
        store.fail_after_commit = False
        append_and_verify(store, "test-cooler", op)
        self.assertEqual(len(store.ops), 1)

    def test_unconfirmed_upload_is_not_reported_as_success(self):
        baseline = base()
        store = FakeJournal(baseline)
        store.fail_before_commit = True
        op = edit(baseline, replay(baseline, []), {"meta.notes": "One"}, 1)
        with self.assertRaisesRegex(JournalError, "unverified"):
            append_and_verify(store, "test-cooler", op)
        self.assertEqual(store.ops, [])

    def test_two_live_chats_with_interleaved_appends_converge(self):
        baseline = base()
        store = FakeJournal(baseline)
        seen_a = replay(store.read_baseline("test-cooler"), store.list_operations("test-cooler"))
        seen_b = replay(store.read_baseline("test-cooler"), store.list_operations("test-cooler"))
        a = edit(baseline, seen_a, {"meta.notes": "Remote included"}, 1)
        b = edit(baseline, seen_b, {"meta.price.quick_sale_rub": 1850}, 2)
        append_and_verify(store, "test-cooler", a)
        final = append_and_verify(store, "test-cooler", b)
        self.assertEqual(final.state["meta"]["notes"], "Remote included")
        self.assertEqual(final.state["meta"]["price"]["quick_sale_rub"], 1850)
        self.assertEqual(len(store.ops), 2)

    def test_duplicate_operation_is_idempotent_but_collision_fails(self):
        baseline = base()
        before = replay(baseline, [])
        a = edit(baseline, before, {"meta.notes": "A"}, 1)
        self.assertEqual(len(replay(baseline, [a, a]).operation_ids), 1)
        tampered = copy.deepcopy(a)
        tampered["edits"]["meta.notes"] = "B"
        with self.assertRaisesRegex(JournalError, "collision"):
            replay(baseline, [a, tampered])

    def test_incomplete_history_fails_closed(self):
        baseline = base()
        a = edit(baseline, replay(baseline, []), {"meta.notes": "A"}, 1)
        b = edit(baseline, replay(baseline, [a]), {"meta.notes": "B"}, 2)
        with self.assertRaisesRegex(JournalError, "missing parent"):
            replay(baseline, [b])

    def test_corrupt_baseline_and_foreign_item_fail(self):
        baseline = base()
        tampered = copy.deepcopy(baseline)
        tampered["meta"]["title"] = "Changed after initialization"
        with self.assertRaisesRegex(JournalError, "baseline hash"):
            replay(tampered, [])
        edit1 = edit(baseline, replay(baseline, []), {"meta.notes": "X"}, 1)
        edit1["item_id"] = "other-item"
        with self.assertRaisesRegex(JournalError, "another item"):
            replay(baseline, [edit1])

    def test_forbid_update_of_id_and_reserved_fields(self):
        baseline = base()
        view = replay(baseline, [])
        for key in ("meta.id", "meta.sync.listing_sha256", "meta.photos.post_count"):
            with self.subTest(key=key), self.assertRaisesRegex(JournalError, "protected"):
                make_operation(baseline, view, {key: "changed"})

    def test_concurrent_listing_edits_conflict(self):
        baseline = base()
        before = replay(baseline, [])
        a = edit(baseline, before, {"listing": "# Cooler\nOne version"}, 1)
        b = edit(baseline, before, {"listing": "# Cooler\nSecond version"}, 2)
        merged = replay(baseline, [a, b])
        self.assertIn("listing", merged.conflicts)
        with self.assertRaises(JournalConflict):
            project_target("test-cooler", "test-cooler", merged)

    def test_concurrent_logs_do_not_mutate_original_state(self):
        baseline = base()
        old = copy.deepcopy(baseline)
        op = edit(baseline, replay(baseline, []), {"meta.notes": "One"}, 1)
        replay(baseline, [op])
        self.assertEqual(old, baseline)


if __name__ == "__main__":
    unittest.main()
