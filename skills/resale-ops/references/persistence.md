# Persistence: cloud queue (default)

The skill targets **phone → agent → PC** with **no dependency on a local `Resale/` path**. State lives in **Google Drive and Google Sheets by default**, loaded via MCP and/or [project memory](persistent-config.md).

Google Drive stores files and Google Sheets stores the Queue dashboard. Other providers and local-only storage are explicit owner-selected alternatives. Check actual connector read/write capabilities; do not require local sync, a service account or a persistent PC path for the default workflow. If cloud tools are missing, explain the dependency and prepare in chat without claiming persistence.

## Canonical layout (in cloud)

```text
Resale/
  .resale-locations.json    ← IDs + defaults (see locations.md)
  queue/<item-id>/
    inbox/                  ← owner uploads from phone
    photos/original/          ← optional archive after sanitization
    photos/post/              ← posting copies only
    listing.md
    meta.json
```

Spreadsheet **Queue** tab = dashboard (`status`, prices, `folder_url`). Full copy stays in `listing.md`.

## Agent responsibilities (cloud / MCP)

1. **Load locations** per [locations.md](locations.md) before creating items.
2. **`init` item** — create `queue/<item-id>/` and subfolders via cloud MCP; write starter `meta.json` and `listing.md` as cloud files.
3. **Photos** — after owner uploads to `inbox/`:
   - Download inbox files to a **temporary workspace** when needed.
   - Run sanitization/compression (`scripts/resale_queue.py prepare-photos` on that temp tree, or equivalent Pillow steps: strip EXIF, resize, JPEG).
   - Upload results to `photos/post/`; move or archive originals to `photos/original/` in cloud if policy requires.
   - Set `meta.json` `photos.metadata_status` to `stripped_verified` only after sanitization actually ran.
4. **Research & copy** — update `listing.md` and `meta.json`; set `status` (`draft` → `researching` → `ready`).
5. **Index** — upsert a row on the **Queue** sheet via Sheets MCP (or append/update by `id`). Do not require `queue-index.csv` on disk.
6. **Handoff** — PC posting uses cloud `photos/post/` (web Drive or sync). List file names and folder link; no marketplace automation in `prepare_only`.

## Optional: local sync + scripts

Owners with **Google Drive for desktop** (or similar) may set `local.resale_root` in locations JSON and run `scripts/resale_queue.py` against that path. This is an **accelerator**, not part of the portable skill contract.

## Status values

| status | Meaning |
|--------|---------|
| `draft` | Folder created; photos or copy incomplete |
| `researching` | Identification/pricing in progress |
| `ready` | `listing.md` complete, `photos/post/` sanitized, prices set |
| `posted` | Owner published (URLs in `posted`) |

## Boundaries

- Cloud persistence does **not** authorize marketplace login, form fill, or upload.
- No passwords, 2FA, or marketplace cookies in `meta.json` or sheets.
- Reference image URLs in `listing.md` unless owner saved licensed copies to `photos/post/`.

Google recipe: [drive-sheets-queue.md](drive-sheets-queue.md).
