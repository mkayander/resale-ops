# Persistent config (cloud-first)

The portable skill does **not** assume a repo or synced disk. Prefer:

1. **Project memory / rules** — paste JSON from [project-memory-snippet.md](../skills/resale-ops/references/project-memory-snippet.md) into ChatGPT project instructions, Cursor rules, Claude `CLAUDE.md`, etc.
2. **Cloud file** — the private `.resale-locations.json` file inside the `Resale` Drive folder (read via Drive MCP in fresh chats).

Full guide: [persistent-config.md](../skills/resale-ops/references/persistent-config.md).

Optional (developers with a local sync folder): [resale-locations.example.json](../resale-locations.example.json) and `python scripts/resale_locations.py validate`.

Cursor template: [templates/cursor-rules/resale-ops.mdc](../templates/cursor-rules/resale-ops.mdc)

## ChatGPT Projects

Use the [single getting-started guide with the complete copyable template](../GETTING-STARTED.md).
Choose GitHub-link mode (fetch SKILL.md and relevant references in each new chat)
or upload a complete workflow snapshot. A skills.sh link alone is not an
installation; failed retrieval must be reported. Connections and write capabilities
must be checked separately.
