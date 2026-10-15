"""Copy one portable skill; no network, config mutation or overwrite."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = {"codex": ".agents", "claude": ".claude", "cursor": ".cursor"}

def install(agent, destination):
    base = Path(destination).expanduser().resolve()
    target = base / LOCATIONS[agent] / "skills" / "avito-seller"
    source = ROOT / "skills" / "avito-seller"
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"Refusing to overwrite: {target}")
    # Reject redirected parent directories, even if the final target is absent.
    for parent in (target.parent, target.parent.parent, base):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError(f"Refusing redirected install directory: {parent}")
    if not target.resolve().is_relative_to(base):
        raise ValueError("Target escapes selected destination")
    shutil.copytree(source, target)
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
