# Google Drive queue + optional Google Sheets

Full developer copy of the portable guide lives in the skill:

[skills/resale-ops/references/drive-sheets-queue.md](../skills/resale-ops/references/drive-sheets-queue.md)

Also see [persistence](../skills/resale-ops/references/persistence.md) and the folder template [templates/resale-queue/README.md](../templates/resale-queue/README.md).

## Quick start (repo checkout)

```sh
python -m pip install -r requirements-queue.txt
export RESALE_ROOT="/path/to/synced/Resale"
python scripts/resale_queue.py --root "$RESALE_ROOT" init my-item-slug
```

Copy [templates/resale-queue/resale-config.example.json](../templates/resale-queue/resale-config.example.json) to `Resale/.resale-config.json` if you want checked-in defaults.
