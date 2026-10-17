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

## ChatGPT Project workflow snapshot

Use the full [ChatGPT project instructions template](chatgpt-project-instructions.md)
with actual Drive/Sheets IDs. Choose GitHub-link mode to fetch SKILL.md and relevant references in each new
chat, or upload all files / a consolidated readable snapshot. Report failed
retrieval; never claim missing files were read or silently substitute an older
upload. A skills.sh link is a discovery source, not an installed skill or
guaranteed per-chat fetch. A main-branch URL may change between chats; use the
same commit SHA for the skill and references when the owner wants a fixed version.
Keep uploaded snapshots stable until the owner requests an update. Verify the workflow
file and actual cloud capabilities in a fresh project chat; never equate IDs with
access, a Drive search connection with write tools, or instructions with photo
processing capability. Missing tools must be reported without claiming success.
