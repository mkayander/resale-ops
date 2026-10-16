# Persistent locations (use every session)

Load this **before** creating items or asking the owner for folder IDs again. IDs are not secrets, but treat them as owner-specific configuration.

## Resolution order

1. **`RESALE_LOCATIONS`** — absolute path to a JSON file (highest priority).
2. **Workspace** — `resale-locations.json` in the project root (or sales project root).
3. **User config** — `~/.config/resale-ops/locations.json` (all platforms) or `~/.resale-ops/locations.json`.
4. **Cloud queue copy** — if Google Drive MCP is available, read `.resale-locations.json` in the owner’s `Resale` folder (same JSON schema).
5. **Legacy** — `README-resale-ops.txt` in `Resale` on Drive.

If nothing is found, ask once, then tell the owner to save config per [persistent-config.md](persistent-config.md) so future chats skip setup.

## JSON schema (`version`: 1)

| Field | Use |
|-------|-----|
| `drive.resale_folder_id` | Root `Resale` folder |
| `drive.queue_folder_id` | `Resale/queue` (create items here) |
| `drive.*_url` | Optional links for the owner |
| `sheets.spreadsheet_id` | Index spreadsheet |
| `sheets.queue_tab` | Usually `Queue` |
| `local.resale_root` | Synced path for `scripts/resale_queue.py` (optional) |
| `defaults.city`, `defaults.platforms`, `defaults.language` | Fill gaps only; explicit user message overrides |

## After loading

- New item folders go under `queue/<item-id>/` (Drive MCP: parent `queue_folder_id`).
- Update the **Queue** sheet tab when `meta.json` status or prices change.
- Do not re-prompt for spreadsheet/folder IDs unless the file is missing or invalid.

## Owner one-time setup

See [persistent-config.md](persistent-config.md) for Cursor rules, ChatGPT/Claude project memory, and copying the example file.
