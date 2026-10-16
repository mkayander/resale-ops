# Persistent config (folder IDs, sheet ID, defaults)

Goal: **one-time setup**, then any chat can say “use resale-ops, new item from inbox” without re-pasting Drive/Sheets links.

## 1. Canonical file (recommended)

From a [resale-ops](https://github.com/mkayander/resale-ops) checkout, copy `resale-locations.example.json` to:

- **`resale-locations.json`** in your project (gitignored), or
- **`~/.config/resale-ops/locations.json`** (works in any project)

Optional: `export RESALE_LOCATIONS="/absolute/path/to/locations.json"`

The agent resolves paths per [locations.md](locations.md).

### Drive copy (fresh chats + phone)

Upload the same JSON as **`Resale/.resale-locations.json`**. With Google Drive MCP, the agent reads it even when no local file exists.

## 2. Cursor

- **Project rules:** copy `templates/cursor-rules/resale-ops.mdc` from the repo into `.cursor/rules/` and replace `REPLACE_ME` or point to `resale-locations.json`.
- **User rules (global):** “For resale, load `~/.config/resale-ops/locations.json` and follow resale-ops.”
- **Cloud agents:** commit `resale-locations.json` to a **private** repo or set `RESALE_LOCATIONS` in the environment.

## 3. ChatGPT

- **Project instructions:** paste filled `resale-locations.json` + “Follow resale-ops.”
- **Project knowledge / files:** attach `resale-locations.json`.
- **Memory:** short line with folder and spreadsheet IDs (optional).

## 4. Claude Code / Codex

- Project `resale-locations.json` or global `~/.config/resale-ops/locations.json`.
- **CLAUDE.md** / **AGENTS.md:** “Load locations per resale-ops `references/locations.md`.”

## 5. Validate (repo checkout)

```sh
python scripts/resale_locations.py validate
python scripts/resale_locations.py show
```

## 6. IDs from URLs

- Folder: `https://drive.google.com/drive/folders/FOLDER_ID`
- Sheet: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

Set `defaults.city`, `defaults.platforms`, `defaults.language` for your usual listings.
