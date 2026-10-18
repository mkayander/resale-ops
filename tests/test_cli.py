"""CLI-level regressions for batch photo processing options."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.cli import main
from resale_queue.meta import init_item


class BatchPhotoCliTest(unittest.TestCase):
    def _batch(self, archive: bool):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items = [init_item(root, slug) for slug in ("one", "two")]
            for item in items:
                Image.new("RGB", (48, 48), "blue").save(item / "inbox" / "original.png")
            args = ["--root", str(root), "prepare-all", "--max-bytes", "200000"]
            if archive:
                args.append("--archive-originals")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                main(args)
            report = json.loads(output.getvalue())
            self.assertEqual(len(report), 2)
            self.assertEqual(sum(x["files"] for x in report), 2)
            for item in items:
                self.assertTrue((item / "photos/post/01.jpg").is_file())
                self.assertFalse((item / "inbox/original.png").exists())
                self.assertEqual((item / "photos/original/original.png").exists(), archive)
                meta = json.loads((item / "meta.json").read_text(encoding="utf-8"))
                self.assertEqual(meta["photos"]["metadata_status"], "stripped_verified")

    def test_prepare_all_does_not_archive_by_default(self):
        self._batch(archive=False)

    def test_prepare_all_explicit_archive_option(self):
        self._batch(archive=True)


if __name__ == "__main__":
    unittest.main()
