# Default queue: Google Drive + Google Sheets

The default is a connected cloud workflow: Google Drive stores photos, listing
text and item metadata; Google Sheets shows the Queue dashboard. The owner uploads
photos from their phone and posts the prepared listing manually from their PC.

Start with the [step-by-step guide](../GETTING-STARTED.md). Connect Drive and Sheets
in the AI host, check actual photo/file and spreadsheet read/write capabilities,
then create or reuse the private Resale folder and dedicated Queue spreadsheet.
Installation alone does not connect either service. Search-only Drive access does
not support maintaining the queue.

- [Cloud setup and first-item workflow](../skills/resale-ops/references/drive-sheets-queue.md)
- [Item layout, statuses and sanitization](../skills/resale-ops/references/persistence.md)
- [Remember folder and spreadsheet IDs](PERSISTENT-CONFIG.md)

No persistent local folder, desktop synchronization or owner-managed service
account is needed for the normal connected workflow. Photo sanitization may
require temporary processing tools; if unavailable, report the gap and leave the
item unready rather than claiming EXIF was removed.

## Optional: local sync or another provider

Use a local path, another cloud provider or CSV dashboard only when the owner
chooses it. For the local Python utilities, a repository checkout and real
synced/local path are required:

```sh
python -m pip install -r requirements-queue.txt
python scripts/resale_queue.py --root /path/to/Resale init my-item-slug
```

Configuration example: [resale-config.example.json](../templates/resale-queue/resale-config.example.json).
Local layout: [queue template](../templates/resale-queue/README.md).
Run `index` to generate CSV/JSON. The optional Sheets API `sheet-push` command
requires separate credentials and replaces the destination sheet body; it is not
the default connector-based row-update workflow.
