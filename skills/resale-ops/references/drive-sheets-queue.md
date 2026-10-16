# Google Drive queue + optional Google Sheets

Portable setup guide (installed with the skill). Repo checkout also ships `scripts/resale_queue.py` and `requirements-queue.txt`.

Cross-device workflow: **phone** uploads photos into a Drive-synced folder; **agent** researches, sanitizes photos, writes `listing.md`; **PC** posts from `photos/post/` using the same folder or a Sheets checklist.

This does **not** auto-configure Google OAuth or MCP. Sync files with [Google Drive for desktop](https://www.google.com/drive/download/) (or rclone). Sheets sync is optional via a **service account**.

## 1. Create the Resale folder

1. Create a folder in Google Drive, e.g. `Resale`.
2. Install Google Drive for desktop and sync that folder on PC.
3. Optional: `Resale/.resale-config.json` with `photo.max_edge`, `photo.max_bytes`, `sheet.spreadsheet_id`.

Set `RESALE_ROOT` to the absolute synced path. See [persistence](persistence.md) for layout.

## 2. Install queue tooling

From a clone of [resale-ops](https://github.com/mkayander/resale-ops):

```sh
python -m pip install -r requirements-queue.txt
```

## 3. Commands

```sh
export RESALE_ROOT="/path/to/Resale"

python scripts/resale_queue.py --root "$RESALE_ROOT" init <slug>
python scripts/resale_queue.py --root "$RESALE_ROOT" prepare-photos <item-id>
python scripts/resale_queue.py --root "$RESALE_ROOT" prepare-all
python scripts/resale_queue.py --root "$RESALE_ROOT" index
python scripts/resale_queue.py --root "$RESALE_ROOT" sheet-push
```

**Phone:** upload to `Resale/queue/<item-id>/inbox/`.  
**Agent:** write `listing.md`, update `meta.json`, run `prepare-photos` before `status: ready`.  
**PC:** post from `photos/post/` only.

## 4. Photo sanitization defaults

| Setting | Default |
|--------|---------|
| Longest edge | 2048 px |
| Target size | 2 MB JPEG |
| Metadata | stripped on save |

`meta.json` → `photos.metadata_status`: `stripped_verified` after `prepare-photos`.

## 5. Optional Google Sheets

Dashboard columns: `id`, `status`, `title`, `city`, `list_price_rub`, `quick_sale_rub`, `metadata_status`, `post_photo_count`, `prepared_at`, `updated_at`, `folder_name`, `drive_folder_url`, `notes`.

1. Create sheet tab `Queue`.
2. Service account + Sheets API; share sheet with service account email.
3. `export GOOGLE_APPLICATION_CREDENTIALS=...` and `export RESALE_SHEET_ID=...`
4. Run `index` then `sheet-push`.

Without API: import `queue-index.csv` into the sheet manually.

## 6. Security

No credentials or queue photos in public git. Prefer city in `meta.json`, not street address. Limit sharing on `photos/original/`.
