# Google Drive + Google Sheets (optional recipe)

One supported way to implement [persistence](persistence.md). **iCloud, Dropbox, OneDrive, NAS, or a local folder** work the same if `RESALE_ROOT` points at the synced tree and `scripts/resale_queue.py` can run there.

Repo checkout ships `scripts/resale_queue.py` and `requirements-queue.txt`.

## Why Google here

Drive desktop sync and Sheets are widely used; `sheet-push` automates index upload via the Sheets API. If you use another provider, skip `sheet-push` and use **`queue-index.csv`** in Excel, Numbers, Notion, Airtable, etc.

## 1. Create the Resale folder in Drive

1. Create `Resale` in Google Drive.
2. Install [Google Drive for desktop](https://www.google.com/drive/download/) (or rclone to a local path).
3. Optional: `Resale/.resale-config.json` with `photo.max_edge`, `photo.max_bytes`, `sheet.spreadsheet_id`.

Set `RESALE_ROOT` to the absolute synced path.

## 2. Install queue tooling

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
python scripts/resale_queue.py --root "$RESALE_ROOT" sheet-push   # Google only
```

## 4. Photo sanitization

See [persistence](persistence.md). Defaults: 2048 px edge, ~2 MB JPEG, metadata stripped.

## 5. Google Sheets index (optional)

Columns match `queue-index.csv`: `id`, `status`, `title`, `city`, `list_price_rub`, `quick_sale_rub`, `metadata_status`, `post_photo_count`, `prepared_at`, `updated_at`, `folder_name`, `folder_url`, `notes`.

1. Tab named `Queue`.
2. Service account + Sheets API; share the spreadsheet with the service account email.
3. `export GOOGLE_APPLICATION_CREDENTIALS=...` and `export RESALE_SHEET_ID=...`
4. `index` then `sheet-push`.

Without API: upload or import `queue-index.csv` into Drive/Sheets manually.

## 6. Security

No credentials or queue photos in public git. Prefer city in `meta.json`, not street address. Limit sharing on `photos/original/`.
