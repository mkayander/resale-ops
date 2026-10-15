"""Offline package checks; not a replacement for official schema validation."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(root=ROOT):
    skill = root / "skills/resale-ops"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), "Missing frontmatter"
    front, body = text[4:].split("\n---\n", 1)
    fields = dict(line.split(": ", 1) for line in front.splitlines())
    name = fields["name"]
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name), "Invalid name"
    assert name == skill.name and len(name) <= 64
    assert 1 <= len(fields["description"]) <= 1024
    assert len(fields.get("compatibility", "")) <= 500
    assert len(text.splitlines()) < 500
    for link in re.findall(r"\]\(([^)]+)\)", body):
        path = (skill / link).resolve()
        assert path.is_relative_to(skill.resolve()) and path.is_file(), link
    portable = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert portable["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert portable["name"] == claude["name"]
    assert portable["version"] == claude["version"]
    assert not (root / "mcp.json").exists(), "Unexpected automatic MCP wiring"
    research = json.loads((root / "examples/ru-marketplace-mcp.client.json").read_text(encoding="utf-8"))
    servers = research["mcpServers"]
    assert set(servers) == {"resale-market-research"}, "Unexpected server in research profile"
    server = servers["resale-market-research"]
    assert server["command"] == "uv"
    assert server["args"][-1] == "compare-mcp" and "--frozen" in server["args"]
    assert server["env"] == {"MARKETPLACE_SOURCES": "yandex_market"}, "Research profile must not enable all sources or CDP"
    print("PASS: frontmatter, references, manifests and package boundaries")

if __name__ == "__main__":
    check()
