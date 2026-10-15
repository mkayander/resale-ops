"""Copy one portable skill; no network, config mutation or overwrite."""
import argparse
import os
import shutil
import stat
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = {"codex": ".agents", "claude": ".claude", "cursor": ".cursor"}


def reject_redirects(path):
    """Check before resolve(), including Windows junctions on Python 3.10+."""
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ValueError(f"Refusing redirected path: {candidate}")


def install(agent, destination):
    if agent not in LOCATIONS:
        raise ValueError(f"Unknown agent: {agent}")
    base = Path(destination).expanduser().absolute()
    target = base / LOCATIONS[agent] / "skills" / "resale-ops"
    source = ROOT / "skills" / "resale-ops"
    reject_redirects(target)
    reject_redirects(source)
    if os.path.lexists(target):
        raise FileExistsError(f"Refusing to overwrite: {target}")
    target = target.resolve()
    source = source.resolve()
    if target.is_relative_to(source):
        raise ValueError("Install destination must be outside the packaged skill")
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"Missing skill source: {source}")
    # copytree follows links by default. Reject them before copying any data.
    for entry in source.rglob("*"):
        reject_redirects(entry)
        if not entry.is_file() and not entry.is_dir():
            raise ValueError(f"Unsupported source entry: {entry}")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Build beside the destination so copy failures never leave a partial skill.
    with tempfile.TemporaryDirectory(prefix=".resale-ops-", dir=target.parent) as tmp:
        staged = Path(tmp) / "resale-ops"
        shutil.copytree(source, staged)
        reject_redirects(target)
        if os.path.lexists(target):
            raise FileExistsError(f"Refusing to overwrite: {target}")
        staged.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=LOCATIONS, required=True)
    parser.add_argument("--destination", required=True, help="Project directory, or home for personal installation")
    args = parser.parse_args()
    try:
        print(f"Installed: {install(args.agent, args.destination)}")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Installation failed: {exc}\n")


if __name__ == "__main__":
    main()
