import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class InstallTest(unittest.TestCase):
    def test_all_clients_copy_complete_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            for agent, location in installer.LOCATIONS.items():
                target = installer.install(agent, Path(tmp).resolve())
                self.assertEqual(target, Path(tmp).resolve() / location / "skills/resale-ops")
                source = ROOT / "skills/resale-ops"
                files = [p for p in source.rglob("*") if p.is_file()]
                self.assertTrue(files)
                for file in files:
                    self.assertEqual(file.read_bytes(), (target / file.relative_to(source)).read_bytes())

    def test_refuses_overwrite_and_preserves_customization(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = installer.install("codex", Path(tmp).resolve())
            file = target / "SKILL.md"
            file.write_text("user customization", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install("codex", Path(tmp).resolve())
            self.assertEqual(file.read_text(encoding="utf-8"), "user customization")

    def test_rejects_install_inside_source_before_writing(self):
        source = ROOT / "skills/resale-ops"
        for relative in (".", "references", "references/not-created"):
            with self.subTest(relative=relative):
                destination = source / relative
                with patch.object(installer.shutil, "copytree") as copy:
                    with self.assertRaisesRegex(ValueError, "outside the packaged skill"):
                        installer.install("codex", destination)
                    copy.assert_not_called()
                self.assertFalse((destination / ".agents").exists())

    def test_copy_failure_leaves_no_partial_skill_and_can_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / ".agents/skills/resale-ops"

            def interrupted_copy(source, staged):
                staged.mkdir()
                (staged / "SKILL.md").write_text("partial", encoding="utf-8")
                raise OSError("disk full")

            with patch.object(installer.shutil, "copytree", side_effect=interrupted_copy):
                with self.assertRaisesRegex(OSError, "disk full"):
                    installer.install("codex", destination)
            self.assertFalse(target.exists())
            self.assertEqual(list(target.parent.iterdir()), [])
            self.assertEqual(installer.install("codex", destination), target)

    def make_redirect(self, link, destination, directory=True):
        try:
            link.symlink_to(destination, target_is_directory=directory)
        except OSError as exc:
            if os.name != "nt" or not directory:
                self.skipTest(f"Symlinks unavailable: {exc}")
            # Real Windows junction exercises Python 3.10/3.11 support too.
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "New-Item -ItemType Junction -Path $env:REVIEW_LINK -Target $env:REVIEW_TARGET | Out-Null"],
                env={**os.environ, "REVIEW_LINK": str(link), "REVIEW_TARGET": str(destination)},
                capture_output=True,
            )
            if result.returncode:
                self.skipTest("Cannot create a Windows junction")

    def test_rejects_redirected_destination_and_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            outside = base / "outside"
            outside.mkdir()
            redirect = base / "redirect"
            self.make_redirect(redirect, outside)
            for destination in (redirect, redirect / "nested/project"):
                with self.subTest(destination=destination):
                    with self.assertRaisesRegex(ValueError, "redirected"):
                        installer.install("codex", destination)
            project = base / "project"
            project.mkdir()
            self.make_redirect(project / ".agents", outside)
            with self.assertRaisesRegex(ValueError, "redirected"):
                installer.install("codex", project)
            self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_redirected_source_without_copying_external_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            source = base / "repo/skills/resale-ops"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("test", encoding="utf-8")
            outside = base / "private"
            outside.mkdir()
            (outside / "secret.txt").write_text("private", encoding="utf-8")
            self.make_redirect(source / "linked", outside)
            with patch.object(installer, "ROOT", base / "repo"):
                with self.assertRaisesRegex(ValueError, "redirected"):
                    installer.install("codex", base / "sales")
            self.assertFalse((base / "sales").exists())

    def test_refuses_existing_file_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            target = base / ".agents/skills/resale-ops"
            target.parent.mkdir(parents=True)
            target.write_text("user file", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                installer.install("codex", base)
            self.assertEqual(target.read_text(encoding="utf-8"), "user file")
            target.unlink()
            target.mkdir()
            with self.assertRaises(FileExistsError):
                installer.install("codex", base)
            self.assertTrue(target.is_dir())

if __name__ == "__main__":
    unittest.main()
