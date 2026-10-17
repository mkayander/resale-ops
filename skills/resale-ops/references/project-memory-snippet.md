# Paste into project instructions / rules

Replace `REPLACE` values, then save in ChatGPT project instructions, Cursor rules, Claude `CLAUDE.md`, etc.

For a ChatGPT Project, use the [complete instructions template](chatgpt-project-instructions.md),
which also covers workflow files, updates, permissions and missing-tool handling.
The compact JSON below remains suitable for other host rules.

## JSON block

```json
{
  "version": 1,
  "drive": {
    "resale_folder_id": "REPLACE",
    "resale_folder_url": "REPLACE",
    "queue_folder_id": "REPLACE",
    "queue_folder_url": "REPLACE"
  },
  "sheets": {
    "spreadsheet_id": "REPLACE",
    "spreadsheet_url": "REPLACE",
    "queue_tab": "Queue"
  },
  "defaults": {
    "city": "REPLACE",
    "platforms": ["avito", "youla"],
    "language": ""
  }
}
```

## Behavior line

When selling items: follow resale-ops skill. Use cloud queue under `queue/<item-id>/` (`inbox/`, `photos/post/`, `listing.md`, `meta.json`). Sanitize photos before `status: ready`. Update the Queue sheet row. Do not ask for folder IDs if this JSON is present. No marketplace login unless owner explicitly requests and an admitted adapter exists.

Duplicate this JSON in cloud as the private `.resale-locations.json` file inside the `Resale` Drive folder for MCP-only sessions.
