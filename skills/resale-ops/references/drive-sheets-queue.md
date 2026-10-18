# Google Drive + Google Sheets (default)

Use this stack unless the owner explicitly chooses another provider or local-only
storage. Drive holds photos and drafts; Sheets holds the Queue dashboard. Follow
[persistence](persistence.md) and [locations](locations.md). A persistent local
folder, desktop sync, Python installation on the owner's PC and service-account
credentials are not required for the default connected workflow.

## 1. Check the connected tools

The host must expose actual capabilities for reading photos, creating folders,
reading/writing Drive files, and reading/updating Sheets rows. Search-only access
is insufficient. The skill does not install connectors or authenticate accounts.
Ask the owner to connect suitable tools through their host and Google sign-in;
never request passwords, login codes, cookies or credential JSON in chat.

Use existing saved locations first. Test only authorized resources and report
which operations are available. If a required capability is absent, explain the
specific setup gap. Continue useful drafting in chat if appropriate, but do not
claim cloud persistence, photo processing or spreadsheet updates succeeded.

## 2. One-time queue setup

With the owner's setup request:

1. Reuse known `Resale`, `queue`, and spreadsheet IDs. Otherwise look for existing
   resources; clarify ambiguous matches rather than creating duplicates.
2. If absent, create `Resale/queue/` in Drive and a dedicated `Resale Queue`
   spreadsheet with a `Queue` tab. Keep access private unless the owner requests
   sharing. Do not modify unrelated resources.
3. Add these headers to the new Queue tab:
   `id`, `status`, `title`, `city`, `list_price_rub`, `quick_sale_rub`,
   `metadata_status`, `post_photo_count`, `prepared_at`, `updated_at`,
   `folder_name`, `folder_url`, `notes`.
   Inspect an existing sheet before editing; preserve its rows, formulas and
   extra columns. Match rows by `id`, not title or row number alone.
4. Save actual returned folder/spreadsheet IDs and URLs in the private
   `.resale-locations.json` file inside the `Resale` Drive folder, using the
   [locations schema](locations.md).
   Show the same configuration for the owner to save in project instructions
   using [persistent-config](persistent-config.md). Never invent IDs or save
   placeholder values as a successful configuration.
5. Return links to Resale, queue and the spreadsheet, with tool evidence of what
   was created or reused. Verify writes by reading the relevant files/rows back.

## 3. First item: phone → agent → manual posting

1. Create a unique `queue/<item-id>/` folder with temporary `inbox/`, permanent
   `photos/post/`, `listing.md` and `meta.json`; do not create `photos/original/`.
   Add one Queue row with `draft`.
   Inspect for an existing item before creating a duplicate. Return the inbox URL.
2. The owner uploads photos of one item through the Drive mobile app or website.
3. Read the selected inbox only. Ask consequential questions, research public
   prices and prepare separate marketplace drafts. Save listing text and metadata
   in Drive and update only the matching Queue row.
4. Create sanitized posting copies with real processing, using a temporary
   workspace when needed, and upload them to `photos/post/`. Verify the upload,
   then delete temporary Drive `inbox/` originals; keep no duplicate or archived originals in Drive.
   If upload fails, retain the original until recovery. No permanent desktop
   sync is needed. Defaults for the optional utility are
   a 2048-pixel edge and a target near 2 MB; inspect actual output size and EXIF.
5. Set `ready` only after drafts, selected price and sanitized photos are complete
   and verified. If photo download, processing or upload is unavailable, retain
   `draft`/`researching`, note the blocker, and provide manual next steps.
6. Return the item-folder and sheet links. The owner checks the final package and
   posts manually. Mark `posted` only from the owner's confirmation or supported
   evidence; label owner-reported URLs/status accordingly.

Do not send photos to another recognition service without consent. Do not make
folders public or claim metadata was removed based only on a proposed operation.
Cloud access never authorizes marketplace login, form entry or publication.


### Safety of repeat runs

The local `sheet-push` is a non-destructive ID-based upsert: it checks existing headers and IDs, updates only matching rows, appends missing rows, then reads the affected values back. It refuses duplicate IDs. It does not remove rows absent from the local index, and must not be used as a way to delete stale cloud items. Parallel edits of **different items** are supported by using server-positioned appends and a fresh ID lookup per item. Do not cache row indexes. A physical deletion exactly between identity check and positional update is still not atomic; avoid deleting rows during writes, or adopt a row-metadata-based provider adapter.

Current local metadata uses nested v2 `price` and `photos` fields. The local indexer normalizes older flat schemas in memory. Do not publish a record with `ready` unless asking price, handoff terms and sanitized photos are confirmed. `photos/post/` holds the only durable photo copies; `--archive-originals` is a deliberate **local-only opt-in**, not for the normal cloud flow.

## Parallel chats adding or removing rows

The common case is **Chat A changes item A while Chat B adds item B**. Keep the Queue as a dashboard indexed by stable item ID, not row number. There is no need to initialize the per-item journal for unrelated items.

- **New item:** check for an existing ID, then append through Sheets itself. In a local Sheets client call `spreadsheets.values.append` with `insertDataOption=INSERT_ROWS`; for connected tools exposing only `batchUpdate`, use `appendCells` with `sheetId` (never a guessed `start.rowIndex`). Read the sheet again and verify exactly one row with the item ID. If the append returns an ambiguous error, search by ID before considering a retry. Multiple appenders of *different* IDs get distinct allocated rows.
- **Update existing item:** read the current ID column and locate exactly one matching row; verify that exact ID again before the write. Patch **only changed columns**, not `A:M` or the full sheet; read back the row by ID, *not* the previously remembered coordinate. Reject duplicate IDs and ambiguous readback. Other items' field changes must be preserved.
- **Rows inserted, reordered or physically deleted in another chat:** discard cached row positions and resolve the target ID afresh. If its position changed after lookup, stop and refresh rather than risk a write to the wrong item. A narrow race remains if a physical deletion happens **between the final identity check and the positional update**: the ordinary Sheets values interface does not offer an atomic conditional row update. For reliable simultaneous physical deletion, a dedicated provider adapter with row-associated developer metadata and `batchUpdateByDataFilter` is required; the default ChatGPT connector does not currently expose that operation in this project. Until then, perform bulk physical deletes while other chat writers are idle. Prefer archiving/filtering during routine work.
- **Deleted rows and data authority:** the Drive item folder, not the Queue row, is the source of item facts. Removing a Queue row does *not* delete its Drive item; the next explicit sync of that item can recreate the row. Permanent item deletion must be a separate owner-authorized workflow, not inferred from an absent spreadsheet row. A missing ID should never trigger deleting any other row.

This is a practical concurrency improvement, not a cross-service database transaction. There is no always-on backend, global sheet lock, new Google login or live Google dependency in mandatory CI. If two chats intentionally edit **the same item**, consult [concurrency.md](concurrency.md) for its opt-in append-only journal.

## Optional: desktop sync and local Python utilities

Only when the owner chooses local sync, use Google Drive for desktop or another
sync client and set `RESALE_ROOT` to the real synced folder. From a repository
checkout, install `requirements-queue.txt`, then run:

```sh
python scripts/resale_queue.py --root /path/to/Resale init my-item
python scripts/resale_queue.py --root /path/to/Resale prepare-photos ITEM_ID
python scripts/resale_queue.py --root /path/to/Resale index
```

Optional local Sheets API upload needs a service account, Sheets API access and
sharing the dedicated spreadsheet with that account. Keep credential files outside
this repository; configure their paths locally, never in chat or public files.
`sheet-push` uses ID-based upserts and **does not clear** the sheet. It does not treat a missing local item as permission to remove a cloud row. Use a dedicated Queue sheet with matching column headers. Without API access, CSV import is a manual alternative.

Other clouds and local CSV dashboards remain available when explicitly selected.
