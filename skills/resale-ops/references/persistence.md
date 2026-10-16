# Persistence: Google Drive queue + optional Sheets

Use when the owner works **phone → agent → PC**. Canonical store: a **Drive-synced** `Resale/` tree. Setup: [drive-sheets-queue.md](drive-sheets-queue.md).

## Layout

```text
Resale/
  queue/<item-id>/
    inbox/              ← owner uploads from phone
    photos/original/    ← archived after processing (optional backup)
    photos/post/        ← only sanitized JPEGs for posting / sync
    listing.md          ← full handoff per references/output.md
    meta.json           ← status, prices, photo metadata_status
  queue-index.json      ← generated; optional Sheets source
```

Ask for `RESALE_ROOT` (absolute path to synced `Resale/`) and item `slug` or existing `item-id`.

## Agent responsibilities

1. **`init`** (new item): tell the owner to run, or run if shell access exists:
   `python scripts/resale_queue.py --root "<RESALE_ROOT>" init <slug>`
2. After owner drops photos in `inbox/`, **always** run before marking photos ready:
   `python scripts/resale_queue.py --root "<RESALE_ROOT>" prepare-photos <item-id>`
   Use `prepare-all` if multiple items have inbox files.
3. Write **`listing.md`** and update **`meta.json`**: `title`, `city`, `list_price_rub`, `quick_sale_rub`, `platforms`, `status` (`draft` → `researching` → `ready`).
4. Set `photos.metadata_status` only from the prepare script output—never claim `stripped_verified` without running it.
5. Run **`index`** after meta changes; run **`sheet-push`** only when owner has configured Google credentials (see doc).
6. In handoff, list **`photos/post/`** filenames in order for PC posting.

## Status values

| status | Meaning |
|--------|---------|
| `draft` | Folder created; photos or copy incomplete |
| `researching` | Identification/pricing in progress |
| `ready` | `listing.md` complete, `photos/post/` processed, prices set |
| `posted` | Owner published (owner-reported URLs in `posted`) |

## Sheets (optional)

Treat Google Sheet as a **filterable index** (`status=ready`). Full text stays in `listing.md`. If API sync is unavailable, owner imports `queue-index.csv`.

## Boundaries

- Persisting to Drive does **not** authorize marketplace login, form fill, or upload.
- Do not store passwords, 2FA, or marketplace cookies in `meta.json` or Sheets.
- Reference product image URLs belong in `listing.md`, not in `photos/post/`, unless the owner saved licensed copies locally.
