# Queue storage (any provider) + Google option

The resale queue is **not tied to Google**. Use any folder that syncs between phone and PC (iCloud, Dropbox, OneDrive, NAS, WebDAV, or a local path). The agent and scripts only need a consistent **`RESALE_ROOT`**.

- **Portable rules:** [skills/resale-ops/references/persistence.md](../skills/resale-ops/references/persistence.md)
- **Google Drive + Sheets recipe:** [skills/resale-ops/references/drive-sheets-queue.md](../skills/resale-ops/references/drive-sheets-queue.md)
- **Folder template:** [templates/resale-queue/README.md](../templates/resale-queue/README.md)

## Quick start (repo checkout)

```sh
python -m pip install -r requirements-queue.txt
export RESALE_ROOT="/path/to/Resale"   # synced or local
python scripts/resale_queue.py --root "$RESALE_ROOT" init my-item-slug
```

Optional config: [templates/resale-queue/resale-config.example.json](../templates/resale-queue/resale-config.example.json) → `Resale/.resale-config.json`.

**Spreadsheet checklist:** run `index`, then open `queue-index.csv` in Excel, Numbers, Notion, Airtable, or import into Google Sheets—no API required.
