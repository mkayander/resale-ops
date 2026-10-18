#!/usr/bin/env python3
"""Blocking quality gates: all tests use local fixtures; never access Google."""
from __future__ import annotations

import subprocess
import sys

CHECKS = [
    [sys.executable, "-m", "ruff", "check", "--select", "E4,E7,E9,F", "scripts", "tests"],
    [sys.executable, "-m", "coverage", "run", "--source=scripts/resale_queue",
     "-m", "unittest", "discover", "-s", "tests", "-q"],
    [sys.executable, "-m", "coverage", "report",
     "--include=scripts/resale_queue/schema.py,scripts/resale_queue/meta.py,"
     "scripts/resale_queue/photos.py,scripts/resale_queue/sheets.py,"
     "scripts/resale_queue/reconcile.py,scripts/resale_queue/concurrent.py",
     "--fail-under=80"],
    [sys.executable, "scripts/verify_archive.py"],
]


def main() -> None:
    for command in CHECKS:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, check=True)
    print("PASS: offline quality gates", flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
