# Deterministic queue reconciliation

Use this procedure when preparing an item, recording owner-reported platform actions, or changing its listing. For concurrent chats, **first** use [concurrency.md](concurrency.md) to append operations; this file describes only how to materialize/retry projections. Using this protocol without the journal is strictly single-writer only. It protects **the saved records** only. It does not authorize access to a marketplace or repeating a submission.

## Single-item unit of work

The stable item ID identifies one existing `queue/<item-id>/` folder, its existing Drive `listing.md` and `meta.json` file IDs, and one Queue row with the same ID. The file IDs must be discovered and reused; **never** create duplicate documents to recover from a failed update. The Queue is a derived index, not a source of truth.

1. **Read:** obtain the listing text, metadata and Queue row for that ID. Verify matching IDs and metadata schema. If an item is already listed or status is unknown, do not create a duplicate marketplace listing.
2. **Prepare one immutable target:** finalize the updated listing, owner-approved price and handoff, photos and provenance. Include its SHA-256 digest in `meta.sync.listing_sha256`. Derive the Queue row from this same metadata object.
3. **Validate before writing:** verify the target status with `validate_meta` and reject mismatching IDs, future schema versions, mismatched photo counts and stale listing digests. Note: the digest proves exact file consistency, **not** that arbitrary free-form listing copy is factually true; the agent must still compare title, price, condition and handoff text with confirmed metadata.
4. **Write in place:** update and read back `listing.md`, then `meta.json`, then upsert and read back the Queue row by item ID. Any step with unverified response must remain reported as unsynced. Do not clear the sheet or overwrite unspecified Queue columns.
5. **Resume safely:** retain the **same initial snapshot and target** for retry. A resource already equal to the target is skipped; a resource still equal to the original can be updated. A third, unexpected value means an external edit: **stop, report a conflict and seek a human decision**, instead of overwriting it. Never repeat marketplace posting to repair tracking.
6. **Report precisely:** success only after all three records are verified. On failure report the completed resource names and unsynced ones. Existing market-side effects remain unchanged.

`scripts/resale_queue/reconcile.py` implements and tests this **provider-neutral** contract (`snapshot`, `make_target`, `reconcile`), including ambiguous responses after a successful write. Its `ItemStore` adapter must be wired to the actual provider. It does **not** itself call Google, mutate the user's Drive, or magically execute inside ChatGPT's connector. Agents using chat tools must apply the same semantics with the actual supported Drive/Sheets operations and must not claim automatic protection by merely reading this document.

## Google provider notes

- Drive: read the current existing file ID; update **that ID** using the provider's supported in-place update method, then read back contents. Library `overwrite=true` is not a portable alternative to Drive `files.update`. Temporary upload is allowed only in the selected private item folder and must be deleted after a verified update, never before.
- Sheets: read the Queue headers and all IDs first. Reject duplicates; update one row with matching ID (patch only changed fields) or append a missing row, and then read it back. If several agents may update the same item, append into the per-item journal; Sheets values API does not offer a row-level compare-and-swap here and its row is a repairable projection.
- If any connector is unavailable, stop at that resource and report the missing capability. Don't reinterpret an unknown result as proof of success or failure.
- Do not store credentials, tokens, exact home addresses, account data or user attachments in the public repository.

## Manual acceptance

Run the offline suite against `FakeStore` and local photos, including the cases where a Queue write fails after Drive is already updated, a write commits but the response is lost, and an external editor changes the listing or row. For a real provider, use only a dedicated private sandbox with owner authorization; live Google smoke is opt-in and cannot block CI.

This procedure is the persistence boundary, **not** an account-automation boundary. Avito/Youla stay in `prepare_only` unless a separately admitted method is explicitly allowed.
