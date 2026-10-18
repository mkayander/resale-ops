# Concurrent chats: append-only item journal (v1)

**Use when more than one chat, agent, or device can update the same item.**
This protocol protects edits in Google Drive without adding an always-on
backend or pretending that Google Sheets has row-level CAS. The Queue,
`listing.md` and `meta.json` are **materialized views** in this mode.
The authoritative record is an immutable item baseline plus all accepted
change files. See the offline reference implementation
`scripts/resale_queue/concurrent.py`.

## Files in each item folder

```text
queue/<item-id>/
  listing.md                 # derived display copy; can temporarily lag
  meta.json                  # derived metadata; can temporarily lag
  photos/post/               # single set of verified photos
  journal/
    baseline.json            # immutable: initial complete listing + meta + hash
    changes/
      <random-uuid-hex>.json # immutable operation, one file for each edit
```

### One-time migration — requires a single writer

Initialize the journal **once** for an existing item before concurrent chats
edit that item. Read the original listing and metadata, generate the baseline
with `make_baseline`, create `journal/baseline.json` in Drive and read it
back. Check that exactly **one** baseline exists and is byte-for-byte valid.
Keep the original `listing.md` and `meta.json` as projections. If two
different baseline files were created concurrently, **stop** and resolve them;
Drive filenames are not uniqueness constraints. Until initialized, use the
previous serialized single-writer protocol. Never recreate or replace an
existing baseline in the normal workflow.

### Every concurrent edit

1. List **all** files under `journal/changes/` (paginate; the first 100
   results are NOT sufficient). Download, parse and validate every operation.
   Read the single baseline. On missing parent, duplicate operation ID with
   differing content, invalid schema, truncated listing, or incomplete page,
   stop and report an error. No blind fallback to stale `meta.json`.
2. Replay the immutable operations using `replay`. The result records a
   deterministic revision and all conflicts. Different metadata leaf fields
   merge regardless of arrival order; changing the same field to different
   values concurrently creates an explicit conflict. A later edit that
   observes **both** competing operation IDs may resolve it.
3. Construct one operation with a fresh random UUID (32 lowercase hex
   characters), the fixed `base_hash`, the **entire observed operation ID
   set**, and a minimal map of leaf changes. Treat `listing` as an
   indivisible field: concurrent listing rewrites conflict. Include any
   dependent listing change in the same operation as a price/terms/condition
   change, then explicitly review the combined result before projecting.
   Owner approval for a changed asking price must be reconfirmed; do not
   reuse authorization tied to an older listing revision.
4. Upload `<operation_id>.json` **as a new raw file**, never update an old
   operation or rename it after success. Re-list and verify by `operation_id`
   and exact contents. If upload reports an error, inspect Drive first:
   **retry only the same operation ID and bytes**, never silently create an
   unrelated second edit. Identical duplicate files are idempotent; different
   data under the same ID is corruption.
5. Re-list and replay the **whole** journal again. If there is a conflict,
   show the two proposals, ask the owner which to keep, and leave the current
   projections untouched. Do not silently choose whichever operation arrived
   first or last. If conflict-free, validate ready-state invariants and
   optionally reconstruct `listing.md`, `meta.json` and Queue by ID.
   Re-read the journal after projection. If new operations appeared, replay
   and project again. After another race (including one right after final
   readback) the projection can be temporarily stale; the journal remains
   recoverable and the next reconciliation must repair it.
6. Report separately **"edit stored in journal"**, **"projection updated"**
   and **"conflict"**. A successful journal append is not a guarantee that
   the current Queue row is up-to-date. Never re-submit a marketplace listing
   just to repair these saved records.

### Important consistency limits

The immutable journal prevents **loss of recorded operations** under
concurrent file overwrites, provided every writer uses it and Drive returns
a complete history. It does **not** give linearizable/transactional writes
across Drive files and Sheets, and it does not solve competing edits to the
same field automatically. The existing `reconcile.py` is the projection
helper for a single consistent target; do not make it the sole source of truth
or bypass the journal while concurrent writers exist.

Reject unsolicited edits of protected identifiers, photo count, schema
version or internal synchronization hashes. Update photos only after
uploading, sanitizing and verifying actual `photos/post/` files; the
journal represents filenames and status but cannot confirm remote bytes.
For platform status and listing URLs, preserve evidence source and do not
infer account actions from a queue projection. No marketplace account is
accessed or published through the journal.

**The Python `JournalStore` Protocol is provider-neutral.** ChatGPT's
Google Drive connector does not execute this Python automatically; agents
must follow the file operations described here using their connected Drive
tools. Existing real items need the one-time baseline initialization.
An optional dedicated cloud adapter can be added later, but should not be
introduced as if it were already deployed.

### Two-chat acceptance

From the same baseline, Chat A edits `meta.notes` and Chat B edits
`meta.price.quick_sale_rub`. Both create different journal files. Replay
contains both updates. When both concurrently edit
`meta.price.list_price_rub` differently, the journal retains both changes,
`replay` returns a conflict and blocks projection until the owner chooses
a version. If Drive is unavailable, preserve the original operation ID and
report `unverified`; never claim a successful save.

No real Google requests or external marketplace calls run in mandatory CI.
See `tests/test_concurrent.py` for synthetic parallel-chat interleavings.
