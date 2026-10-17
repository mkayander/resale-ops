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
4. Save actual returned folder/spreadsheet IDs and URLs in
   `Resale/.resale-locations.json` using the [locations schema](locations.md).
   Show the same configuration for the owner to save in project instructions
   using [persistent-config](persistent-config.md). Never invent IDs or save
   placeholder values as a successful configuration.
5. Return links to Resale, queue and the spreadsheet, with tool evidence of what
   was created or reused. Verify writes by reading the relevant files/rows back.

## 3. First item: phone → agent → manual posting

1. Create a unique `queue/<item-id>/` folder with `inbox/`, `photos/original/`,
   `photos/post/`, `listing.md` and `meta.json`; add one Queue row with `draft`.
   Inspect for an existing item before creating a duplicate. Return the inbox URL.
2. The owner uploads photos of one item through the Drive mobile app or website.
3. Read the selected inbox only. Ask consequential questions, research public
   prices and prepare separate marketplace drafts. Save listing text and metadata
   in Drive and update only the matching Queue row.
4. Create sanitized posting copies with real processing, using a temporary
   workspace when needed, and upload them to `photos/post/`. No permanent desktop
   sync is needed. Preserve originals. Defaults for the optional utility are
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
`sheet-push` replaces the Queue sheet body: use it only for an explicitly selected
dedicated sheet, never a mixed-use spreadsheet tab. This is separate from normal
connector-based row updates. Without API access, CSV import is a manual alternative.

Other clouds and local CSV dashboards remain available when explicitly selected.
