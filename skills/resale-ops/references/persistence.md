# Persistence: cross-device queue

Use when the owner works **phone → agent → PC**. The queue is **provider-agnostic**: any folder tree that syncs or is visible on both devices works. Google Drive and Google Sheets are common choices, not requirements.

## Storage options (pick one)

| Approach | Phone → folder | PC access | Index / checklist |
|----------|----------------|-----------|-------------------|
| **Cloud sync** | iCloud Drive, Dropbox, OneDrive, Google Drive, Synology, etc. | Same sync client or web | `queue-index.csv` in any spreadsheet app |
| **Same machine path** | AirDrop/USB to a folder the agent uses | Local path | `queue-index.json` only |
| **Git private repo** | Push photos + meta (careful with size/secrets) | Pull on PC | Issues/board or CSV |
| **NAS / WebDAV** | Mobile app uploads to `inbox/` | Desktop mount | CSV import |

Requirements: a stable **`RESALE_ROOT`** path on the machine where the agent runs commands, and the same files reachable on PC for posting (sync, mount, or copy).

Google-specific setup: [drive-sheets-queue.md](drive-sheets-queue.md). For Excel, Notion, Airtable, or Apple Numbers, import or paste **`queue-index.csv`** after `index`—no Google API needed.

## Layout

```text
Resale/
  queue/<item-id>/
    inbox/              ← owner uploads from phone
    photos/original/    ← archived after processing (optional backup)
    photos/post/        ← only sanitized JPEGs for posting / sync
    listing.md          ← full handoff per references/output.md
    meta.json           ← status, prices, photo metadata_status
  queue-index.json      ← generated
  queue-index.csv       ← optional dashboard in any spreadsheet tool
```

Ask for `RESALE_ROOT` only when not in [locations](locations.md) (`local.resale_root`) and local `prepare-photos` is needed. For Drive MCP, use saved `drive.queue_folder_id`. Item `slug` or existing `item-id` still required per listing.

## Agent responsibilities

1. **`init`** (new item): tell the owner to run, or run if shell access exists:
   `python scripts/resale_queue.py --root "<RESALE_ROOT>" init <slug>`
2. After owner drops photos in `inbox/`, **always** run before marking photos ready:
   `python scripts/resale_queue.py --root "<RESALE_ROOT>" prepare-photos <item-id>`
   Use `prepare-all` if multiple items have inbox files.
3. Write **`listing.md`** and update **`meta.json`**: `title`, `city`, `list_price_rub`, `quick_sale_rub`, `platforms`, `status` (`draft` → `researching` → `ready`), optional `folder_url` (link to item folder in whatever cloud UI the owner uses).
4. Set `photos.metadata_status` only from the prepare script output—never claim `stripped_verified` without running it.
5. Run **`index`** after meta changes. Run **`sheet-push`** only when the owner uses Google Sheets with API credentials; otherwise point them at `queue-index.csv`.
6. In handoff, list **`photos/post/`** filenames in order for PC posting.

## Status values

| status | Meaning |
|--------|---------|
| `draft` | Folder created; photos or copy incomplete |
| `researching` | Identification/pricing in progress |
| `ready` | `listing.md` complete, `photos/post/` processed, prices set |
| `posted` | Owner published (owner-reported URLs in `posted`) |

## Spreadsheet index (optional)

Any tool that can filter on `status=ready` is fine. Full copy stays in `listing.md`. Regenerate the index with `index`; sync the CSV through the owner’s stack (Drive, Dropbox, email, git, etc.).

## Boundaries

- A synced queue folder does **not** authorize marketplace login, form fill, or upload.
- Do not store passwords, 2FA, or marketplace cookies in `meta.json` or spreadsheets.
- Reference product image URLs belong in `listing.md`, not in `photos/post/`, unless the owner saved licensed copies locally.
