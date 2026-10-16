import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.meta import build_index, init_item, write_index_files
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
            self.assertTrue((item_dir / "photos" / "original" / "big.png").exists())

    def test_empty_inbox_preserves_existing_post_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            item_dir = init_item(Path(tmp), "preserve-post")
            inbox = item_dir / "inbox"
            Image.new("RGB", (100, 100), color="red").save(inbox / "a.png")
            prepare_item_photos(item_dir, PhotoProcessConfig(max_edge=512, max_bytes=200_000))
            write_photo_report(item_dir, prepare_item_photos(item_dir, PhotoProcessConfig()))

            meta = json.loads((item_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["photos"]["post"], ["photos/post/01.jpg"])
            self.assertEqual(meta["photos"]["metadata_status"], "stripped_verified")
            self.assertTrue((item_dir / "photos" / "post" / "01.jpg").is_file())

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
            meta["status"] = "ready"
            (item_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

            rows = build_index(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Chair")
            json_path, csv_path = write_index_files(root, rows)
            self.assertTrue(json_path.is_file())
            self.assertTrue(csv_path.is_file())


if __name__ == "__main__":
    unittest.main()
