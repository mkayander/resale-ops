import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_locations import find_locations, validate


class ResaleLocationsTest(unittest.TestCase):
    def test_validate_accepts_complete_config(self):
        data = {
            "version": 1,
            "drive": {
                "resale_folder_id": "abc",
                "queue_folder_id": "def",
            },
            "sheets": {
                "spreadsheet_id": "ghi",
                "queue_tab": "Queue",
            },
        }
        self.assertEqual(validate(data), [])

    def test_find_locations_respects_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "locations.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "drive": {"resale_folder_id": "a", "queue_folder_id": "b"},
                        "sheets": {"spreadsheet_id": "c", "queue_tab": "Queue"},
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"RESALE_LOCATIONS": str(path)}):
                found, data = find_locations()
            self.assertEqual(found, path)
            self.assertEqual(data["drive"]["resale_folder_id"], "a")


if __name__ == "__main__":
    unittest.main()
