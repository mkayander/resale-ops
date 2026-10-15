"""Offline checks for this package's supported subset, not host certification."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

if __package__:
    from .install import reject_redirects
else:
    from install import reject_redirects

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


class UniqueLoader(yaml.SafeLoader):
    """Duplicate keys should fail instead of silently replacing metadata."""


def unique_mapping(loader, node):
    result = {}
    for key, value in loader.construct_pairs(node):
        require(isinstance(key, str) and key not in result, f"Invalid or duplicate YAML key: {key}")
        result[key] = value
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"Missing frontmatter: {path}")
    parts = text[4:].split("\n---\n", 1)
    require(len(parts) == 2, f"Unclosed frontmatter: {path}")
    fields = yaml.load(parts[0], Loader=UniqueLoader)
    require(isinstance(fields, dict), "Frontmatter must be an object")
    require(set(fields) <= {"name", "description", "license", "compatibility", "metadata"}, "Unexpected skill field")
    name = fields.get("name")
    require(isinstance(name, str) and NAME.fullmatch(name) and len(name) <= 64, "Invalid skill name")
    require(name == path.parent.name, "Skill name differs from directory")
    for key, limit in (("description", 1024), ("compatibility", 500)):
        if key == "description" or key in fields:
            value = fields.get(key)
            require(isinstance(value, str) and value.strip() and len(value) <= limit, f"Invalid {key}")
    if "metadata" in fields:
        require(isinstance(fields["metadata"], dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in fields["metadata"].items()
        ), "metadata must map strings to strings")
    require(fields.get("license") == "MIT", "Expected MIT license")
    require(parts[1].strip() and len(text.splitlines()) < 500, "Missing or oversized skill body")
    return fields


def check_links(root, skill):
    # Check this repository's inline Markdown links, outside fenced code blocks.
    documents = [root / "README.md", *root.glob("docs/*.md"), *skill.rglob("*.md")]
    for document in documents:
        text = re.sub(r"(?ms)^```[^\n]*\n.*?^```[^\n]*$", "", document.read_text(encoding="utf-8"))
        for link in re.findall(r"\]\(([^)]+)\)", text):
            parsed = urlsplit(link.strip("<>"))
            if parsed.scheme in {"https", "http", "mailto"}:
                continue
            require(not parsed.scheme and not parsed.netloc, f"Unsupported link in {document}: {link}")
            if not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            boundary = skill if document.is_relative_to(skill) else root
            require(target.is_relative_to(boundary) and target.is_file(), f"Broken or escaping link in {document}: {link}")


def check_manifest(manifest, portable):
    require(isinstance(manifest, dict), "Manifest must be an object")
    allowed = {"name", "version", "description", "license", "repository", "homepage", "author", "keywords"}
    if portable:
        allowed |= {"$schema", "extensions"}
        require(manifest.get("$schema") == SCHEMA, "Invalid portable schema")
    require(set(manifest) <= allowed, "Unexpected manifest fields (automatic tools are not supported)")
    require(manifest.get("name") == "resale-ops", "Manifest name differs from skill")
    require(isinstance(manifest.get("version"), str) and VERSION.fullmatch(manifest["version"]), "Expected numeric release version")
    for key in ("description", "license", "repository", "homepage"):
        if key in manifest:
            require(isinstance(manifest[key], str) and manifest[key].strip(), f"Invalid manifest {key}")
    if "keywords" in manifest:
        require(isinstance(manifest["keywords"], list) and all(isinstance(k, str) for k in manifest["keywords"]), "Invalid keywords")
    if "author" in manifest:
        author = manifest["author"]
        require(isinstance(author, dict) and set(author) <= {"name", "email", "url"}
                and all(isinstance(v, str) for v in author.values()), "Invalid author")
    require(not manifest.get("extensions"), "Client extensions need separate review")


def check(root=ROOT):
    root = Path(root).resolve()
    skill = root / "skills/resale-ops"
    for entry in skill.rglob("*"):
        reject_redirects(entry)
    read_frontmatter(skill / "SKILL.md")
    require((skill / "LICENSE").read_bytes() == (root / "LICENSE").read_bytes(), "Standalone skill must carry the complete license")
    check_links(root, skill)
    portable = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    check_manifest(portable, portable=True)
    check_manifest(claude, portable=False)
    require(portable["version"] == claude["version"], "Manifest versions differ")
    package_json = root / "package.json"
    if package_json.is_file():
        package = json.loads(package_json.read_text(encoding="utf-8"))
        require(
            isinstance(package.get("version"), str) and VERSION.fullmatch(package["version"]),
            "Invalid package.json version",
        )
        require(package["version"] == portable["version"], "package.json version differs from plugin.json")
    readme = (root / "README.md").read_text(encoding="utf-8")
    require(f"Версия {portable['version']}." in readme, "README version differs")
    for relative in ("mcp.json", ".mcp.json", ".cursor/mcp.json", ".claude/settings.json", ".codex/config.toml"):
        require(not (root / relative).exists(), f"Unexpected automatic client configuration: {relative}")
    # An "inspection" label cannot restrict the tools exposed by a full server.
    # Do not distribute runnable client profiles until an adapter is admitted.
    for folder in (root / "examples", skill, root / "docs"):
        for path in folder.rglob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            require(not isinstance(data, dict) or "mcpServers" not in data,
                    f"Runnable MCP client profile requires security review: {path}")
    print("PASS: metadata, documentation links, licenses, manifests and package boundaries")


def main():
    try:
        check()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        sys.exit(f"Package check failed: {exc}")


if __name__ == "__main__":
    main()
