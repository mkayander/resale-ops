# Persistent locations (cloud-first, every session)

The skill is **global**: it must work without a fixed disk, synced folder, or repo checkout. Load IDs and defaults **before** asking the owner again.

## Resolution order (highest first)

1. **Host project memory / rules** — Cursor project or user rules, ChatGPT project instructions, Claude project `CLAUDE.md`, Codex `AGENTS.md`, or equivalent. Look for a `resale-locations` JSON block (schema below) or explicit folder/spreadsheet IDs. This is the **preferred** store when the host provides it.

2. **Cloud config file (MCP)** — When Drive (or another cloud) MCP is connected, read **`.resale-locations.json`** in the owner’s `Resale` folder. Same JSON schema. Works in a fresh chat with no local files.

3. **Legacy cloud readme** — `README-resale-ops.txt` in `Resale` on Drive.

4. **Local files (optional)** — Only if the runtime has a real filesystem and the owner uses offline scripts: `RESALE_LOCATIONS`, `./resale-locations.json`, or `~/.config/resale-ops/locations.json`. **Do not require these** for normal skill operation.

If nothing is found, ask **once**, then tell the owner to add the JSON to **project instructions/rules** and to **`Resale/.resale-locations.json`** per [persistent-config.md](persistent-config.md).

## JSON schema (`version`: 1)

```json
{
  "version": 1,
  "drive": {
    "resale_folder_id": "...",
    "queue_folder_id": "...",
    "resale_folder_url": "...",
    "queue_folder_url": "..."
  },
  "sheets": {
    "spreadsheet_id": "...",
    "queue_tab": "Queue",
    "spreadsheet_url": "..."
  },
  "defaults": {
    "city": "",
    "platforms": ["avito", "youla"],
    "language": ""
  }
}
```

`local.resale_root` is **optional** — only for owners who run `scripts/resale_queue.py` against a synced path. Cloud-only owners omit it.

## After loading

- Create item folders under `queue/<item-id>/` via cloud MCP (`queue_folder_id` as parent).
- Persist `listing.md`, `meta.json`, and photos in cloud storage—not only in chat.
- Update the spreadsheet **Queue** tab via Sheets MCP when status or prices change.
- Apply `defaults` only when the user did not override city/language/platforms in the message.
