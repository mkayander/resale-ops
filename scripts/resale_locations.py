#!/usr/bin/env python3
"""Load and validate resale-locations.json from standard paths."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DRIVE = ("resale_folder_id", "queue_folder_id")
REQUIRED_SHEETS = ("spreadsheet_id", "queue_tab")


def candidate_paths() -> list[Path]:
    paths: list[Path] = []
    env = os.environ.get("RESALE_LOCATIONS", "").strip()
    if env:
        paths.append(Path(env).expanduser())
    paths.append(ROOT / "resale-locations.json")
    paths.append(Path.home() / ".config" / "resale-ops" / "locations.json")
    paths.append(Path.home() / ".resale-ops" / "locations.json")
    return paths


def find_locations() -> tuple[Path | None, dict[str, Any]]:
    for path in candidate_paths():
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"{path}: root must be an object")
            return path, data
    return None, {}


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("version") != 1:
        errors.append("version must be 1")
    drive = data.get("drive")
    if not isinstance(drive, dict):
        errors.append("drive must be an object")
    else:
        for key in REQUIRED_DRIVE:
            value = drive.get(key, "")
            if not isinstance(value, str) or not value.strip() or "PASTE" in value:
                errors.append(f"drive.{key} must be set")
    sheets = data.get("sheets")
    if not isinstance(sheets, dict):
        errors.append("sheets must be an object")
    else:
        for key in REQUIRED_SHEETS:
            value = sheets.get(key, "")
            if not isinstance(value, str) or not value.strip() or "PASTE" in value:
                errors.append(f"sheets.{key} must be set")
    return errors


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "show"
    path, data = find_locations()
    if command == "show":
        if path is None:
            print("No resale-locations file found. Candidates:")
            for candidate in candidate_paths():
                print(f"  - {candidate}")
            sys.exit(1)
        print(json.dumps({"path": str(path), "config": data}, ensure_ascii=False, indent=2))
        return
    if command == "validate":
        if path is None:
            sys.exit("No resale-locations file found")
        errors = validate(data)
        if errors:
            sys.exit("Invalid config:\n- " + "\n- ".join(errors))
        print(f"OK: {path}")
        return
    if command == "path":
        if path is None:
            sys.exit(1)
        print(path)
        return
    sys.exit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
