# Browser protocol for admitted adapters

Read [account safety](account-safety.md) and the [platform registry](platforms.md) first. Avito and Youla remain manual-final-action platforms: an explicit owner request may authorize assisted browser steps, but never unattended publication. Local test forms without real accounts are allowed for adapter development.

## Tool boundary

Tool availability is not admission. Inspect current schemas for reading, input, and upload instead of assuming tool names or arguments. For authorized work, use a reviewed pinned version and a dedicated task profile. Never run `@latest` beside an account or connect the user’s entire personal browser. The user logs in and solves CAPTCHA manually.

Do not export storage state/cookies, expose remote debugging to a network, or request broad file access. Giving a local path to remote MCP neither makes the file available nor authorizes transfer. Origin allowlists help but do not replace URL/redirect/permission checks. Browser tools may expose eval, unrelated tabs, and arbitrary controls; prompt restrictions are not technical isolation. Remain manual if access cannot be constrained.

## Sequence

`permission → origin/account/item → inspect → fill/upload → inspect → compare → stop`

1. Verify exact HTTPS hostname, owner-agreed account and item, and no existing listing/duplicate. Reject shorteners and “seller verification” links from listings.
2. Confirm a new form or unpublished draft. If it is live or status is unknown, stop before input because autosave may alter public fields.
3. Match visible labels and values. Take a fresh snapshot after navigation or category changes. Never use stale coordinates, hidden APIs, or blind selectors.
4. Recheck origin before every input/upload. Upload only selected, inspected, metadata-sanitized copies. Verify count, order, cover photo, and errors.
5. Before Next/Save/Import, determine consequences. Never press Enter to submit; Save may publish, submit for moderation, or consume quota.
6. Read values back. Use `draft_saved` only with explicit UI evidence; otherwise use `form_filled` and warn that closing may lose data.
7. A human performs the final action by default. Admitted automated submission requires explicit approval of the specific final version; payment requires separate approval.

No parallel/background actions or repeated login. A normal transient failure may be retried once only after checking state and only when it was not a submission. After a CAPTCHA, pause automation while the owner solves it; resume only the same admitted method after the owner’s confirmation. Never switch transport after CAPTCHA, 401/403/429, account restriction, or challenge. For ambiguous submission outcome, check status through an admitted method or ask the user—never resubmit.

Statuses: `prepared`, `form_filled`, `draft_saved`, `blocked`, `submitted`, `published`. Always state whether the agent observed the status through an admitted method or the owner reported it. Never infer an upgrade.

## CDP and Chrome DevTools MCP

For the Windows/WSL flow:

1. Launch a dedicated Chrome profile from PowerShell:

   ```powershell
   & "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" `
     --remote-debugging-port=9222 `
     --user-data-dir="$env:TEMP\resale-ops-cdp"
   ```

2. Log in and solve CAPTCHA manually. Confirm the listener in `chrome://inspect/#remote-debugging`.
3. If Chrome reports `[::1]:9222`, run the MCP process in the Windows context with a pinned version and `--browserUrl http://[::1]:9222`; do not assume WSL `127.0.0.1` reaches it.
4. Inspect the active tab, exact origin, account, item, and page state before input. Use page-scoped routing when several tabs are open.
5. Fill and verify the draft, then stop for the owner’s final publication action.

Keep the listener local and use a dedicated profile. CDP connectivity does not itself authorize an operation.
