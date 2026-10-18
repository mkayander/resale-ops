import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.meta import build_index, init_item, write_index_files
from resale_queue.schema import normalize_meta, validate_meta, to_queue_row
from resale_queue.sheets import plan_upserts, SHEET_HEADERS
from resale_queue.photos import PhotoProcessConfig, prepare_item_photos, write_photo_report


class ResaleQueueTest(unittest.TestCase):
    def test_init_and_prepare_photos_strips_and_resizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item_dir = init_item(root, "test-chair")
            inbox = item_dir / "inbox"
            source = inbox / "big.png"
            Image.new("RGB", (3000, 2000), color=(120, 80, 40)).save(source)

            report = prepare_item_photos(item_dir, PhotoProcessConfig(max_edge=1024, max_bytes=500_000))
            self.assertEqual(len(report["post"]), 1)
            post = item_dir / "photos" / "post" / "01.jpg"
            self.assertTrue(post.is_file())
            with Image.open(post) as image:
                self.assertLessEqual(max(image.size), 1024)
                self.assertFalse(image.getexif())

            self.assertFalse((inbox / "big.png").exists())
            self.assertFalse((item_dir / "photos" / "original").exists())

    def test_empty_inbox_preserves_existing_post_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            item_dir = init_item(Path(tmp), "preserve-post")
            inbox = item_dir / "inbox"
            Image.new("RGB", (100, 100), color="red").save(inbox / "a.png")
            prepare_item_photos(item_dir, PhotoProcessConfig(max_edge=512, max_bytes=200_000))
            write_photo_report(item_dir, prepare_item_photos(item_dir, PhotoProcessConfig()))

            meta = json.loads((item_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["photos"]["prepared_filenames"], ["01.jpg"])
            self.assertEqual(meta["photos"]["metadata_status"], "stripped_verified")
            self.assertTrue((item_dir / "photos" / "post" / "01.jpg").is_file())

    def test_existing_exif_blocks_mixed_collection_and_keeps_inbox_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = init_item(Path(tmp), "mixed-exif")
            post_dir = item / "photos/post"
            exif = Image.Exif()
            exif[0x010E] = "private information"
            Image.new("RGB", (90, 60), "red").save(post_dir / "01.jpg", exif=exif)
            incoming = item / "inbox/new.jpg"
            Image.new("RGB", (90, 60), "green").save(incoming)

            with self.assertRaisesRegex(ValueError, "without EXIF"):
                prepare_item_photos(item, PhotoProcessConfig(max_bytes=200_000))

            self.assertTrue(incoming.exists())
            self.assertFalse((post_dir / "02.jpg").exists())
            meta = json.loads((item / "meta.json").read_text(encoding="utf-8"))
            self.assertNotEqual(meta["photos"]["metadata_status"], "stripped_verified")

    def test_existing_untracked_jpeg_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = init_item(Path(tmp), "untracked-photo")
            Image.new("RGB", (40, 40), "blue").save(item / "photos/post/raw.jpg")
            Image.new("RGB", (40, 40), "blue").save(item / "inbox/new.png")
            with self.assertRaisesRegex(ValueError, "untracked"):
                prepare_item_photos(item, PhotoProcessConfig(max_bytes=200_000))
            self.assertTrue((item / "inbox/new.png").is_file())

    def test_mixed_verified_photos_produce_verified_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = init_item(Path(tmp), "verified-mixed")
            Image.new("RGB", (40, 40), "blue").save(item / "photos/post/01.jpg")
            Image.new("RGB", (40, 40), "green").save(item / "inbox/new.png")
            report = prepare_item_photos(item, PhotoProcessConfig(max_bytes=200_000))
            self.assertEqual(report["metadata_status"], "stripped_verified")
            self.assertEqual(report["post"], ["photos/post/01.jpg", "photos/post/02.jpg"])
            write_photo_report(item, report)
            meta = json.loads((item / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["photos"]["post_count"], 2)

    def test_photo_names_continue_past_99_and_keep_numeric_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = init_item(Path(tmp), "many-photos")
            post = item / "photos/post"
            Image.new("RGB", (40, 40), "blue").save(post / "99.jpg")
            Image.new("RGB", (40, 40), "red").save(post / "02.jpg")
            Image.new("RGB", (40, 40), "green").save(item / "inbox/new.png")
            report = prepare_item_photos(item, PhotoProcessConfig(max_bytes=200_000))
            self.assertEqual(report["post"], [
                "photos/post/02.jpg", "photos/post/99.jpg", "photos/post/100.jpg"
            ])
            write_photo_report(item, report)
            meta = json.loads((item / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["photos"]["prepared_filenames"][-1], "100.jpg")
            self.assertEqual(meta["photos"]["post_count"], 3)

    def test_sold_and_archived_preserve_metadata_without_ready_requirements(self):
        for status in ("sold", "archived"):
            with self.subTest(status=status):
                meta = validate_meta({"id": "test-item", "status": status,
                                      "notes": "owner_reported"})
                self.assertEqual(meta["status"], status)
                self.assertEqual(to_queue_row(meta, "test-item")["status"], status)
        with self.assertRaisesRegex(ValueError, "invalid item status"):
            validate_meta({"id": "test-item", "status": "deleted"})

    def test_incremental_inbox_appends_post_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            item_dir = init_item(Path(tmp), "incremental")
            inbox = item_dir / "inbox"
            Image.new("RGB", (80, 80), color="blue").save(inbox / "first.png")
            prepare_item_photos(item_dir, PhotoProcessConfig(max_edge=512, max_bytes=200_000))
            Image.new("RGB", (80, 80), color="green").save(inbox / "second.png")
            report = prepare_item_photos(item_dir, PhotoProcessConfig(max_edge=512, max_bytes=200_000))

            self.assertEqual(report["post"], ["photos/post/01.jpg", "photos/post/02.jpg"])
            self.assertTrue((item_dir / "photos" / "post" / "02.jpg").is_file())

    def test_index_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item_dir = init_item(root, "index-test")
            meta = json.loads((item_dir / "meta.json").read_text(encoding="utf-8"))
            meta["title"] = "Chair"
            meta["status"] = "draft"
            (item_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

            rows = build_index(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Chair")
            json_path, csv_path = write_index_files(root, rows)
            self.assertTrue(json_path.is_file())
            self.assertTrue(csv_path.is_file())


    def test_future_schema_version_is_rejected_without_mutation(self):
        raw = {"id": "test-chair", "schema_version": 3}
        with self.assertRaisesRegex(ValueError, "unsupported metadata schema"):
            normalize_meta(raw)
        self.assertEqual(raw["schema_version"], 3)

    def test_mismatched_photo_count_or_legacy_price_is_rejected(self):
        bad = {"id": "test-chair", "photos": {"prepared_filenames": ["01.jpg"],
               "post_count": 4}}
        with self.assertRaisesRegex(ValueError, "post_count"):
            validate_meta(bad)
        bad = {"id": "test-chair", "list_price_rub": 1000,
               "price": {"list_price_rub": 2000}}
        with self.assertRaisesRegex(ValueError, "conflicting"):
            validate_meta(bad)

    def test_listing_digest_shape_is_validated(self):
        with self.assertRaisesRegex(ValueError, "listing_sha256"):
            validate_meta({"id": "test-chair", "sync": {"listing_sha256": "oops"}})

    def test_legacy_flat_metadata_migrates_without_mutation(self):
        legacy = {"id": "old-item", "status": "draft", "title": "Item",
                  "list_price_rub": 1200, "quick_sale_rub": 900,
                  "platforms": ["avito"], "photos": {"post": ["photos/post/01.jpg"]}}
        updated = normalize_meta(legacy)
        self.assertEqual(updated["schema_version"], 2)
        self.assertEqual(updated["price"]["list_price_rub"], 1200)
        self.assertEqual(updated["photos"]["prepared_filenames"], ["01.jpg"])
        self.assertNotIn("price", legacy)
        self.assertEqual(to_queue_row(updated, "old-item")["post_photo_count"], 1)

    def test_realistic_cloud_metadata_indexes_price_and_photos(self):
        meta = {"id": "chigo-fkl-ml139r-20261018", "title": "CHIGO", "city": "Москва",
                "status": "ready", "pickup_location": "Москва, метро Севастопольская",
                "price": {"list_price_rub": 2900, "quick_sale_rub": 1900,
                          "price_selected_by_owner": True},
                "photos": {"prepared_filenames": ["01_chigo_front.jpg",
                                                   "02_chigo_side.jpg"],
                           "metadata_status": "stripped_verified"}}
        row = to_queue_row(meta, meta["id"])
        self.assertEqual(row["list_price_rub"], 2900)
        self.assertEqual(row["post_photo_count"], 2)

    def test_ready_gate_enforces_owner_price_handoff_and_photos(self):
        base = {"id": "test-chair", "title": "Chair", "city": "Москва",
                "status": "ready", "price": {"list_price_rub": 1000,
                "price_selected_by_owner": True},
                "photos": {"prepared_filenames": ["01.jpg"],
                           "metadata_status": "stripped_verified"}}
        with self.assertRaisesRegex(ValueError, "handoff"):
            validate_meta(base)
        base["pickup_location"] = "Москва"
        validate_meta(base)
        base["price"]["price_selected_by_owner"] = False
        with self.assertRaisesRegex(ValueError, "owner-approved"):
            validate_meta(base)

    def test_sheets_upsert_preserves_other_rows_and_rejects_duplicates(self):
        existing = [SHEET_HEADERS, ["other-item", "ready"], ["my-item", "draft"]]
        actions = plan_upserts(existing, [{"id": "my-item", "status": "ready"},
                                          {"id": "new-item", "status": "draft"}])
        self.assertEqual([row for row, _ in actions], [3, 4])
        self.assertEqual(existing[1][0], "other-item")
        with self.assertRaisesRegex(ValueError, "duplicate Queue"):
            plan_upserts([SHEET_HEADERS, ["same"], ["same"]], [{"id": "same"}])
        with self.assertRaisesRegex(ValueError, "duplicate update"):
            plan_upserts(existing, [{"id": "my-item"}, {"id": "my-item"}])
        with self.assertRaisesRegex(ValueError, "headers"):
            plan_upserts([["bad"]], [{"id": "my-item"}])

    def test_oversized_photo_keeps_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            item_dir = init_item(Path(tmp), "too-big")
            source = item_dir / "inbox" / "one.png"
            Image.new("RGB", (32, 32), color="orange").save(source)
            with self.assertRaisesRegex(ValueError, "byte limit"):
                prepare_item_photos(item_dir, PhotoProcessConfig(max_bytes=2))
            self.assertTrue(source.exists())
            self.assertFalse((item_dir / "photos/post/01.jpg").exists())

    def test_index_rejects_wrong_folder_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item_dir = init_item(root, "chair")
            meta = json.loads((item_dir / "meta.json").read_text())
            meta["id"] = "another-chair"
            (item_dir / "meta.json").write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError, "ID mismatch"):
                build_index(root)

if __name__ == "__main__":
    unittest.main()
