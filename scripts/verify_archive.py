#!/usr/bin/env python3
"""Build and verify the distribution ZIP without network access or credentials."""
from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "resale-ops/"
REQUIRED = (
    "README.md",
    "LICENSE",
    "plugin.json",
    ".claude-plugin/plugin.json",
    "skills/resale-ops/SKILL.md",
    "scripts/check_package.py",
    "scripts/install.py",
)
PRIVATE_NAMES = {
    "resale-locations.json",
    ".resale-locations.json",
    ".env",
    "credentials.json",
}


def verify_archive() -> None:
    with tempfile.TemporaryDirectory(prefix="resale-ops-archive-") as tmp:
        workspace = Path(tmp)
        archive = workspace / "package.zip"
        subprocess.run(
            ["git", "archive", "--format=zip", "--prefix=" + PREFIX,
             "--output=" + str(archive), "HEAD"],
            cwd=ROOT, check=True,
        )
        with ZipFile(archive) as payload:
            entries = payload.infolist()
            if not entries:
                raise ValueError("distribution archive is empty")
            for entry in entries:
                name = entry.filename
                if not name.startswith(PREFIX):
                    raise ValueError(f"archive entry outside package: {name}")
                relative = name[len(PREFIX):]
                parts = Path(relative).parts
                if any(part in {"..", ".git", "__pycache__"} for part in parts):
                    raise ValueError(f"unsafe archive path: {name}")
                if parts and (parts[-1] in PRIVATE_NAMES or parts[-1].endswith((".pem", ".key"))):
                    raise ValueError(f"private file in distribution: {name}")
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symlink in distribution: {name}")
            present = {entry.filename for entry in entries}
            missing = [name for name in REQUIRED if PREFIX + name not in present]
            if missing:
                raise ValueError(f"required distribution files missing: {missing}")
            payload.extractall(workspace)

        unpacked = workspace / "resale-ops"
        commands = [
            [sys.executable, "scripts/check_package.py"],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        ]
        for command in commands:
            subprocess.run(command, cwd=unpacked, check=True)
        print("PASS: clean distribution ZIP, package integrity and offline tests")


if __name__ == "__main__":
    try:
        verify_archive()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Distribution verification failed: {exc}")
