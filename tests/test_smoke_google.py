"""The optional Google check must never contact Google without sandbox setup."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SmokeIsolationTest(unittest.TestCase):
    def test_unconfigured_smoke_is_skipped_without_network(self):
        env = dict(os.environ)
        for name in ("GOOGLE_SMOKE_CREDENTIALS_JSON", "GOOGLE_SMOKE_FOLDER_ID",
                     "GOOGLE_SMOKE_SPREADSHEET_ID"):
            env.pop(name, None)
        result = subprocess.run(
            [sys.executable, "scripts/smoke_google.py"],
            cwd=ROOT, env=env, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKIPPED", result.stdout)


if __name__ == "__main__":
    unittest.main()
