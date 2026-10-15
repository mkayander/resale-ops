import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class InstallTest(unittest.TestCase):
    def test_all_clients_copy_complete_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            for agent, location in installer.LOCATIONS.items():
                target = installer.install(agent, tmp)
                self.assertEqual(target, Path(tmp).resolve() / location / "skills/resale-ops")
                source = ROOT / "skills/resale-ops"
                files = [p for p in source.rglob("*") if p.is_file()]
                self.assertTrue(files)
                for file in files:
                    self.assertEqual(file.read_bytes(), (target / file.relative_to(source)).read_bytes())

    def test_refuses_overwrite_and_preserves_customization(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = installer.install("codex", tmp)
            file = target / "SKILL.md"
            file.write_text("user customization", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install("codex", tmp)
            self.assertEqual(file.read_text(encoding="utf-8"), "user customization")

if __name__ == "__main__":
    unittest.main()
