"""Mocked Sheets API integration checks; no Google credentials or live writes."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.sheets import upsert_rows, SHEET_HEADERS


class FakeOperation:
    def __init__(self, callback):
        self.callback = callback

    def execute(self):
        return self.callback()


class FakeValues:
    def __init__(self, initial, fail_update=False, corrupt=False, formatted_readback=False):
        self.table = [list(row) for row in initial]
        self.fail_update = fail_update
        self.corrupt = corrupt
        self.formatted_readback = formatted_readback
        self.read_options = []
        self.updates = []
        self.clear_calls = 0

    def get(self, *, spreadsheetId, range, valueRenderOption=None):
        def fetch():
            self.read_options.append(valueRenderOption)
            rows = [list(x) for x in self.table]
            if self.formatted_readback and self.updates and valueRenderOption != "UNFORMATTED_VALUE":
                for row in rows[1:]:
                    if len(row) > 4 and isinstance(row[4], (int, float)):
                        row[4] = f"{row[4]:,} RUB"

            if self.corrupt and self.updates:
                rows[-1][1] = "externally-changed"
            return {"values": rows}
        return FakeOperation(fetch)

    def update(self, *, spreadsheetId, range, valueInputOption, body):
        def save():
            if self.fail_update:
                raise RuntimeError("simulated connector failure")
            self.updates.append(range)
            import re
            match = re.search(r"!A(\d+):M\d+$", range)
            assert match, range
            index = int(match.group(1)) - 1
            while len(self.table) <= index:
                self.table.append([])
            self.table[index] = list(body["values"][0])
            return {}
        return FakeOperation(save)

    def clear(self, **kwargs):
        self.clear_calls += 1
        raise AssertionError("destructive clear is forbidden")


class FakeService:
    def __init__(self, values):
        self.provider = values

    def spreadsheets(self):
        return self

    def values(self):
        return self.provider


class CloudSyncRegressionTest(unittest.TestCase):
    def test_upsert_preserves_unrelated_records_and_is_repeatable(self):
        v = FakeValues([SHEET_HEADERS, ["other-item", "ready"],
                        ["my-item", "draft"]])
        s = FakeService(v)
        data = {"id": "my-item", "status": "ready",
                "title": "Updated", "list_price_rub": 2900}
        self.assertEqual(upsert_rows(s, "test", "Queue", [data]), 1)
        self.assertEqual(v.table[1][0:2], ["other-item", "ready"])
        self.assertEqual(v.table[2][0:3], ["my-item", "ready", "Updated"])
        self.assertEqual(upsert_rows(s, "test", "Queue", [data]), 1)
        self.assertEqual(len(v.table), 3)
        self.assertEqual(v.clear_calls, 0)

    def test_currency_formatting_does_not_break_verified_readback(self):
        v = FakeValues([SHEET_HEADERS, ["my-item", "draft"]], formatted_readback=True)
        upsert_rows(FakeService(v), "test", "Queue", [
            {"id": "my-item", "status": "ready", "list_price_rub": 2900}
        ])
        self.assertEqual(v.read_options, ["UNFORMATTED_VALUE", "UNFORMATTED_VALUE"])
        self.assertEqual(v.table[1][4], 2900)

    def test_partial_index_does_not_delete_other_items(self):
        v = FakeValues([SHEET_HEADERS, ["existing", "ready"]])
        upsert_rows(FakeService(v), "test", "Queue", [{"id": "new"}])
        self.assertEqual(len(v.table), 3)
        self.assertEqual(v.table[1][0], "existing")
        self.assertEqual(v.table[2][0], "new")

    def test_failed_write_does_not_clear(self):
        v = FakeValues([SHEET_HEADERS, ["other", "ready"]], fail_update=True)
        with self.assertRaisesRegex(RuntimeError, "simulated connector"):
            upsert_rows(FakeService(v), "test", "Queue", [{"id": "new"}])
        self.assertEqual(len(v.table), 2)
        self.assertEqual(v.clear_calls, 0)

    def test_readback_detects_changed_row(self):
        v = FakeValues([SHEET_HEADERS, ["one", "draft"]], corrupt=True)
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            upsert_rows(FakeService(v), "test", "Queue",
                        [{"id": "one", "status": "ready"}])

    def test_duplicate_cloud_rows_stop_before_write(self):
        v = FakeValues([SHEET_HEADERS, ["repeat"], ["repeat"]])
        with self.assertRaisesRegex(ValueError, "duplicate Queue"):
            upsert_rows(FakeService(v), "test", "Queue", [{"id": "repeat"}])
        self.assertFalse(v.updates)


if __name__ == "__main__":
    unittest.main()
