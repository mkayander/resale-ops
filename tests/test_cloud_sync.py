"""Mocked Sheets API integration checks; no Google credentials or live writes."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resale_queue.sheets import upsert_rows, SHEET_HEADERS, QueueConflict


class FakeOperation:
    def __init__(self, callback):
        self.callback = callback

    def execute(self):
        return self.callback()


class FakeValues:
    def __init__(self, initial, fail_update=False, corrupt=False,
                 formatted_readback=False, numeric_as_float=False):
        self.table = [list(row) for row in initial]
        self.fail_update = fail_update
        self.corrupt = corrupt
        self.formatted_readback = formatted_readback
        self.numeric_as_float = numeric_as_float
        self.read_options = []
        self.updates = []
        self.appends = []
        self.clear_calls = 0
        self.before_identity = None
        self.before_append = None
        self.after_batch_update = None

    def get(self, *, spreadsheetId, range, valueRenderOption=None):
        def fetch():
            self.read_options.append(valueRenderOption)
            import re
            identity = re.search(r"!A(\d+)$", range)
            if identity:
                if self.before_identity:
                    callback, self.before_identity = self.before_identity, None
                    callback(self)
                index = int(identity.group(1)) - 1
                return {"values": [[self.table[index][0]]] if
                        index < len(self.table) and self.table[index] else []}
            rows = [list(x) for x in self.table]
            if self.numeric_as_float:
                for row in rows[1:]:
                    for index in (4, 5, 7):
                        if index < len(row) and isinstance(row[index], int):
                            row[index] = float(row[index])
            if self.formatted_readback and self.updates and valueRenderOption != "UNFORMATTED_VALUE":
                for row in rows[1:]:
                    if len(row) > 4 and isinstance(row[4], (int, float)):
                        row[4] = f"{row[4]:,} RUB"
            if self.corrupt and self.updates:
                rows[-1][1] = "externally-changed"
            return {"values": rows}
        return FakeOperation(fetch)

    def batchUpdate(self, *, spreadsheetId, body):
        def save():
            if self.fail_update:
                raise RuntimeError("simulated connector failure")
            import re
            for data in body["data"]:
                match = re.search(r"!([A-M])(\d+)$", data["range"])
                assert match, data["range"]
                row_index = int(match.group(2)) - 1
                col_index = ord(match.group(1)) - ord("A")
                while len(self.table[row_index]) <= col_index:
                    self.table[row_index].append("")
                self.table[row_index][col_index] = data["values"][0][0]
                self.updates.append(data["range"])
            if self.after_batch_update:
                callback, self.after_batch_update = self.after_batch_update, None
                callback(self)
            return {}
        return FakeOperation(save)

    def append(self, *, spreadsheetId, range, valueInputOption,
               insertDataOption, body):
        def save():
            if self.fail_update:
                raise RuntimeError("simulated connector failure")
            if self.before_append:
                callback, self.before_append = self.before_append, None
                callback(self)
            assert insertDataOption == "INSERT_ROWS"
            self.table.append(list(body["values"][0]))
            self.appends.append(self.table[-1][0])
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
        self.assertEqual(v.read_options, ["UNFORMATTED_VALUE"] * 3)
        self.assertEqual(v.table[1][4], 2900)

    def test_partial_index_does_not_delete_other_items(self):
        v = FakeValues([SHEET_HEADERS, ["existing", "ready"]])
        upsert_rows(FakeService(v), "test", "Queue", [{"id": "new"}])
        self.assertEqual(len(v.table), 3)
        self.assertEqual(v.table[1][0], "existing")
        self.assertEqual(v.table[2][0], "new")

    def test_equivalent_numeric_float_readback_is_accepted(self):
        v = FakeValues([SHEET_HEADERS, ["my-item", "draft"]], numeric_as_float=True)
        self.assertEqual(upsert_rows(FakeService(v), "test", "Queue", [
            {"id": "my-item", "status": "ready", "list_price_rub": 2900,
             "quick_sale_rub": 1900, "post_photo_count": 3}
        ]), 1)
        self.assertEqual(v.table[1][4], 2900)

    def test_partial_patch_retains_price_photo_count_and_notes(self):
        existing = [SHEET_HEADERS, [
            "my-item", "draft", "Original title", "Москва", 2900, 1900,
            "stripped_verified", 3, "2026-10-18", "2026-10-18",
            "my-item", "https://drive.google.com/folder", "owner confirmed"
        ]]
        fake = FakeValues(existing)
        upsert_rows(FakeService(fake), "test", "Queue", [
            {"id": "my-item", "status": "ready"}
        ])
        self.assertEqual(fake.table[1][1], "ready")
        self.assertEqual(fake.table[1][2:], existing[1][2:])
        self.assertEqual(fake.clear_calls, 0)

    def test_explicit_clear_does_not_clear_other_fields(self):
        existing = [SHEET_HEADERS, [
            "my-item", "draft", "Original title", "Москва", 2900, 1900,
            "stripped_verified", 3, "2026-10-18", "2026-10-18",
            "my-item", "folder-url", "old notes"
        ]]
        fake = FakeValues(existing)
        upsert_rows(FakeService(fake), "test", "Queue", [
            {"id": "my-item", "notes": None}
        ])
        self.assertEqual(fake.table[1][12], "")
        self.assertEqual(fake.table[1][4], 2900)

    def test_failed_write_does_not_clear(self):
        v = FakeValues([SHEET_HEADERS, ["other", "ready"]], fail_update=True)
        with self.assertRaisesRegex(QueueConflict, "failed or is unverified"):
            upsert_rows(FakeService(v), "test", "Queue", [{"id": "new"}])
        self.assertEqual(len(v.table), 2)
        self.assertEqual(v.clear_calls, 0)

    def test_readback_detects_changed_row(self):
        v = FakeValues([SHEET_HEADERS, ["one", "draft"]], corrupt=True)
        with self.assertRaisesRegex(QueueConflict, "readback mismatch"):
            upsert_rows(FakeService(v), "test", "Queue",
                        [{"id": "one", "status": "ready"}])

    def test_duplicate_cloud_rows_stop_before_write(self):
        v = FakeValues([SHEET_HEADERS, ["repeat"], ["repeat"]])
        with self.assertRaisesRegex(ValueError, "duplicate Queue"):
            upsert_rows(FakeService(v), "test", "Queue", [{"id": "repeat"}])
        self.assertFalse(v.updates)


if __name__ == "__main__":
    unittest.main()
