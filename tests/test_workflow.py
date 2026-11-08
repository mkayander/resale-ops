"""Offline contract test of the complete prepare → confirm → queue handoff."""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.meta import build_index, init_item, load_meta, save_meta
from resale_queue.photos import PhotoProcessConfig, prepare_item_photos, write_photo_report
from resale_queue.sheets import SHEET_HEADERS, plan_upserts


class WorkflowTest(unittest.TestCase):
    def test_item_reaches_ready_without_touching_other_queue_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = init_item(root, "cooler")
            source = item / "inbox" / "original.jpg"
            Image.new("RGB", (160, 120), color="gray").save(source)

            photo_report = prepare_item_photos(
                item, PhotoProcessConfig(max_edge=256, max_bytes=100_000)
            )
            write_photo_report(item, photo_report)
            self.assertFalse(source.exists())

            meta = load_meta(item)
            self.assertEqual(meta["photos"]["metadata_status"], "stripped_verified")
            self.assertEqual(meta["photos"]["prepared_filenames"], ["01.jpg"])
            meta["title"] = "Test cooler"
            meta["city"] = "Москва"
            meta["quantity"] = 2
            meta["status"] = "ready"
            meta["pickup_location"] = "Москва, метро Севастопольская"
            meta["price"].update({
                "list_price_rub": 2900,
                "quick_sale_rub": 1900,
                "price_selected_by_owner": True,
            })
            save_meta(item, meta)
            self.assertEqual(load_meta(item)["status"], "ready")
            (item / "listing.md").write_text("Test cooler, 2900 RUB, pickup in Moscow\n", encoding="utf-8")

            queue = build_index(root)
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["post_photo_count"], 1)
            self.assertEqual(queue[0]["list_price_rub"], 2900)
            self.assertEqual(queue[0]["quantity"], 2)
            self.assertEqual(queue[0]["status"], "ready")
            rows = [SHEET_HEADERS, ["another-item", "posted"], [item.name, "draft"]]
            changes = plan_upserts(rows, queue)
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0][0], 3)
            self.assertEqual(changes[0][1][1], "ready")
            self.assertEqual(rows[1][0:2], ["another-item", "posted"])

    def test_suggested_price_persists_ready_without_owner_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            item = init_item(Path(temp), "pending")
            meta = load_meta(item)
            meta.update({"title": "Item", "city": "Москва", "status": "ready",
                         "pickup_location": "Москва"})
            meta["price"]["list_price_rub"] = 1500
            meta["photos"].update({
                "prepared_filenames": ["01.jpg"],
                "post_count": 1,
                "metadata_status": "stripped_verified",
            })
            save_meta(item, meta)
            saved = load_meta(item)
            self.assertEqual(saved["status"], "ready")
            self.assertFalse(saved["price"]["price_selected_by_owner"])


if __name__ == "__main__":
    unittest.main()
