# Persistent config (cloud-first)

The portable skill does **not** assume a repo or synced disk. Prefer:

1. **Project memory / rules** — paste JSON from [project-memory-snippet.md](../skills/resale-ops/references/project-memory-snippet.md) into ChatGPT project instructions, Cursor rules, Claude `CLAUDE.md`, etc.
2. **Cloud file** — `Resale/.resale-locations.json` (read via Drive MCP in fresh chats).

Full guide: [persistent-config.md](../skills/resale-ops/references/persistent-config.md).

Optional (developers with a local sync folder): [resale-locations.example.json](../resale-locations.example.json) and `python scripts/resale_locations.py validate`.

Cursor template: [templates/cursor-rules/resale-ops.mdc](../templates/cursor-rules/resale-ops.mdc)
