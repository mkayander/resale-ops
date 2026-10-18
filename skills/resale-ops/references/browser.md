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

## Persistent Chrome launch: Windows, macOS and Linux

For an explicit request to open the owner's Resale Ops browser, launch installed
Google Chrome with port 9222 and the same permanent dedicated profile below.
Do not substitute an in-app browser or the everyday Chrome profile. Opening
Chrome does not authorize CDP connection, account inspection, forms or uploads.
The owner handles login and publication manually; adapter admission still applies.

### Windows / PowerShell

```powershell
& "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:LOCALAPPDATA\ResaleOps\ChromeProfile"
```

For per-user Chrome, replace only the executable with
`$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe`; for a 32-bit install
use `${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe`.
From WSL, execute this command through `powershell.exe` so Windows expands the
variables. Reuse Windows Chrome and its Windows profile, not Linux Chrome.

### macOS / Terminal

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/ResaleOps/ChromeProfile"
```

For a per-user installation, replace only `/Applications` in the executable path
with `$HOME/Applications`.

### Linux / desktop shell

```sh
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="${XDG_CONFIG_HOME:-$HOME/.config}/resale-ops/chrome-profile"
```

If the executable is named `google-chrome-stable`, use that name instead.
Installed Chrome and a graphical desktop are required. Keep `XDG_CONFIG_HOME`
consistent between launches.

### Preserve the session

Chrome creates the profile folder. Reuse its location across chats and restarts;
never use TEMP, TMPDIR, /tmp, a checkout or a fresh random directory. Keep the
profile outside source control, cloud sync and package archives.

The owner signs in manually on first use. A new profile does not inherit login
from everyday Chrome or the former temporary profile. Do not migrate cookies,
tokens or storage state. Close and reopen the dedicated Chrome with the same
command to verify persistence. Sites may still expire or revoke sessions; do not
promise permanent login or reset the profile as a routine repair.

Reuse the dedicated running instance. If it was started without debugging, ask
the owner to close its windows normally and relaunch: new flags may not apply
to an existing process. Do not kill other Chrome processes or delete profile
locks. If another process owns port 9222, report the conflict rather than
connecting to an unknown browser.

Keep the debugging listener local to loopback. Never open it to the network,
forward the port or add `--remote-allow-origins=*` to work around connectivity.
Chrome 136+ requires a non-default user data directory for debugging switches:
[Chrome documentation](https://developer.chrome.com/blog/remote-debugging-port).

### CDP and Chrome DevTools MCP (admitted adapters only)

Launching Chrome does not install or admit an adapter. Use a reviewed pinned MCP
version. Confirm the listener in `chrome://inspect/#remote-debugging`; use its
actual loopback endpoint with `--browserUrl`, e.g. `http://127.0.0.1:9222` or
`http://[::1]:9222`. For Windows Chrome, run MCP in the Windows context; do not
assume WSL loopback reaches the Windows listener. Do not expose the port to fix it.

After admission and operation authorization, inspect the exact origin, account,
item and page state before input, using page-scoped routing for multiple tabs.
Follow the sequence above and stop for the owner's final publication action.
CDP connectivity does not itself authorize any account operation.
