# Persistence: cloud queue (default)

The skill targets **phone → agent → PC** with **no dependency on a local `Resale/` path**. State lives in **Google Drive and Google Sheets by default**, loaded via MCP and/or [project memory](persistent-config.md).

Google Drive stores files and Google Sheets stores the Queue dashboard. Other providers and local-only storage are explicit owner-selected alternatives. Check actual connector read/write capabilities; do not require local sync, a service account or a persistent PC path for the default workflow. If cloud tools are missing, explain the dependency and prepare in chat without claiming persistence.

## Canonical layout (in cloud)

```text
Resale/                     ← Google Drive folder
  .resale-locations.json    ← private IDs + defaults file (see locations.md)
  queue/<item-id>/
    inbox/                  ← temporary upload staging; clear after successful processing
    photos/post/              ← sole persistent photo copies (sanitized/compressed)
    listing.md
    meta.json
```

Spreadsheet **Queue** tab = dashboard (`status`, prices, `folder_url`). Full copy stays in `listing.md`.

## Agent responsibilities (cloud / MCP)

1. **Load locations** per [locations.md](locations.md) before creating items.
2. **`init` item** — create `queue/<item-id>/` with temporary `inbox/` and permanent `photos/post/` via cloud MCP; write starter `meta.json` and `listing.md` as cloud files. Do not create `photos/original/`.
3. **Photos** — after owner uploads to `inbox/`:
   - Download inbox files to a **temporary workspace** when needed.
   - Run sanitization/compression (`scripts/resale_queue.py prepare-photos` on that temp tree, or equivalent Pillow steps: strip EXIF, resize, JPEG).
   - Upload selected results to `photos/post/` and verify that each expected file exists and is usable.
   - **Space-saving default:** delete originals from `inbox/` only after corresponding sanitized posting copies are successfully verified. Keep `inbox/` empty between runs. Do not retain `photos/original/` or second photo copies in Drive. If sanitization/upload fails, keep staging inputs until resolved; do not delete the sole existing copy.
   - Photos supplied in chat should be processed from the temporary workspace and uploaded directly to `photos/post/` without uploading originals to Drive.
   - Set `meta.json` `photos.metadata_status` to `stripped_verified` only after sanitization actually ran.
4. **Research & copy** — update `listing.md` and `meta.json`; set `status` (`draft` → `researching` → `ready`).
5. **Index** — upsert a row on the **Queue** sheet via Sheets MCP (or append/update by `id`). Do not require `queue-index.csv` on disk.
6. **Handoff** — PC posting uses cloud `photos/post/` (web Drive or sync). List file names and folder link; no marketplace automation in `prepare_only`.
7. **Reconcile** — after handoff or later changes, follow the state reconciliation below before reporting completion.

## Reconcile state after handoff or changes

For an existing queue item, preparation and subsequent changes are complete only when the saved records agree with the known outcome. An owner report is sufficient to record a change with owner-reported provenance; it does not authorize account access to verify it.

- Read the current `meta.json`, current listing document, and Queue row matched by stable item ID. Reuse their existing file IDs, schema, columns, and links; if a newer draft is already designated current, update it rather than an older `listing.md` or a new competing copy.
- Reconcile the affected fields across all three: platform-specific status and listing URL/ID, selected price, agreed pickup/delivery terms and discounts, and actual uploaded photo filenames/order/count. Preserve unrelated fields and other platforms' statuses. Keep prepared photo inventory separate from uploaded photos; five available files do not prove five uploads.
- Preserve evidence provenance and known observation time. Submission awaiting moderation is `submitted`, not `published`; failed or ambiguous actions do not advance status. Use the existing queue's status vocabulary (for example `posted` for a known publication), and retain per-platform evidence in metadata and the row's notes when dedicated columns are absent.
- Write the affected records in place, then read back each one and compare the changed fields. Only then report both the action result and successful persistence. Do not claim the Queue is current from a Drive write alone.
- If a connector is unavailable, a write fails, or readback disagrees, report which records remain unsynced and the exact change still needed. On continuation, reconcile from the known outcome; never repeat a marketplace submission to repair tracking. A successful marketplace action remains successful even when persistence fails.

Cloud reconciliation changes tracking only; it does not authorize marketplace access or expand an adapter's permitted operations.


## Canonical metadata v2 and safe reconciliation

New local and cloud items use **metadata schema v2**: `price.list_price_rub`, `price.quick_sale_rub`, `price.price_selected_by_owner`, and `photos.prepared_filenames` (basenames under `photos/post/`). `photos.post_count` must equal the number of names. The local queue reader supports older flat files and `photos.post` paths without modifying the original until an explicit save. Do not mix flattened price/photolist fields in a new record. Missing source data stays unknown; do not mark it confirmed.

The queue is a **derived index**, not the authoritative owner of item facts. Treat each item folder's `meta.json` and `listing.md` as canonical; update them in place. `sheet-push` now performs per-ID upserts and never clears the Queue tab. Before modifying a sheet, read headers and IDs, reject duplicates, and on failure leave unrelated rows intact. After writing, read back changed rows and reconcile discrepancies. Sheets lacks transaction-level compare-and-swap in this integration; concurrent writers should be serialized. Do not reconstruct the full sheet from an incomplete local index.

To mark `ready`, require a title, city, owner-selected asking price, sanitized photo filenames with verified metadata status, and agreed pickup or delivery. Missing optional box/instructions or a separate leak check can remain unresolved, explicitly labeled. A final `listing.md` must not retain stale placeholder text claiming price or handoff is unknown. Compare this text against `meta.json` and Queue on readback.

Google Drive connector note: file/library upload with `overwrite=true` may not work. Use an in-place Drive `files.update`-style operation on the **existing file ID** with a valid connector file reference, then fetch and verify; do not create a competing `listing.md` or `meta.json`. If a staging file is required, upload it privately, verify it, update the canonical ID, and delete the staging file only after canonical readback succeeds.

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
- Apply single-copy photo storage to all new items: keep no Drive original/archive copies by default.

Google recipe: [drive-sheets-queue.md](drive-sheets-queue.md).
