"""Create one readable project upload from the canonical skill and references.

This exports instructions only: no plugin installation, credentials or cloud API.
"""
import argparse
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/resale-ops"


def build(output):
    sources = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
    sources.append(SKILL / "LICENSE")
    chunks = [
        "# Resale Ops — ChatGPT project context\n\n"
        "A self-contained workflow snapshot, not an installed plugin. Read the\n"
        "SKILL.md section and the relevant reference sections before resale work.\n"
        "References named below are included in this same document; use their\n"
        "section headings instead of assuming local filesystem access.\n"
        "Google Drive and Google Sheets connections and photo-processing tools\n"
        "must be available separately. Project instructions supply private IDs.\n"
        "Template REPLACE values below are examples, never configured resources.\n"
    ]
    inventory = []
    for source in sources:
        text = source.read_text(encoding="utf-8")
        relative = source.relative_to(SKILL).as_posix()
        inventory.append(f"- `{relative}` — SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`")
        # Flatten local links into section references, retaining external URLs.
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: m[0] if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", m[2])
            else f"{m[1]} (included section: {m[2].removeprefix('references/')})",
            text,
        )
        chunks.append(f"\n---\n\n# Included file: {relative}\n\n{text}\n")
    chunks.insert(1, "\n## Snapshot inventory\n\n" + "\n".join(inventory) + "\n")
    output = Path(output)
    if output.resolve().is_relative_to(SKILL.resolve()):
        raise ValueError("Write the generated snapshot outside the canonical skill")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks), encoding="utf-8")
    return len(sources)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(f"Exported {build(args.output)} source files to {args.output}")
