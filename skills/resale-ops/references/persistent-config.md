# One-time setup (no local disk required)

Goal: paste IDs **once** into the host’s project memory / rules (or a cloud JSON file), then use resale-ops from any device by uploading photos to cloud `inbox/`.

## Recommended: project instructions / rules (ChatGPT, Cursor, Claude)

Copy the block below into:

| Host | Where |
|------|--------|
| **ChatGPT** | Project → Instructions (and optionally attach the same JSON as a project file) |
| **Cursor** | Project rules (e.g. `.cursor/rules/resale-ops.mdc`) or **User rules** for all chats |
| **Claude** | Project instructions or root `CLAUDE.md` |
| **Codex** | `AGENTS.md` in the sales project |

Use [project-memory-snippet.md](project-memory-snippet.md) as a fill-in template.

Add one line of behavior:

> When I mention resale or selling an item, follow the **resale-ops** skill. Load `resale-locations` from these instructions (or Drive `Resale/.resale-locations.json` if MCP is connected). Do not ask for folder IDs again unless missing.

## Cursor Cloud Agents (this repository)

| Layer | Purpose |
|-------|---------|
| `.cursor/rules/resale-ops.mdc` | Project rules — IDs load on every Cloud Agent run for this repo |
| `AGENTS.md` | Cloud entrypoint: skill, MCP, Drive file |
| `.cursor/environment.json` | `install` runs `pip install -r requirements-queue.txt` on the VM |
| Drive `Resale/.resale-locations.json` | Backup when rules are empty; phone-friendly |
| **User rules** (optional) | Paste the same JSON for resale work in **other** repos |

Enable **Google Drive** and **Google Sheets** MCP on [cursor.com/agents](https://cursor.com/agents). Docs: [Cloud setup](https://cursor.com/docs/cloud-agent/setup.md), [Rules](https://cursor.com/docs/rules).

## Also store in cloud (phone + fresh chats)

Upload the **same JSON** as `Resale/.resale-locations.json` in your cloud folder. Agents with **Google Drive MCP** read it even when project rules are empty.

No desktop sync required. The owner uploads photos with the **Drive mobile app** (or equivalent) into `queue/<item-id>/inbox/`.

## Optional: local checkout (developers only)

If you clone [resale-ops](https://github.com/mkayander/resale-ops) and use `scripts/resale_queue.py` on a synced path:

- `resale-locations.example.json` → `resale-locations.json` (gitignored) or `~/.config/resale-ops/locations.json`
- `python scripts/resale_locations.py validate`

This is **not** required for the portable skill in ChatGPT/Cursor cloud chat.

## IDs from URLs

- Folder: `https://drive.google.com/drive/folders/FOLDER_ID`
- Sheet: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

Set `defaults.city` and `defaults.language` for your usual listings.
