# `ru-marketplace-mcp`: source inspection only

Reviewed revision: `cc89f2d87f59b8e2f2858db30a63208d439a7c3f` on 2026-10-15 ([upstream](https://github.com/Vladimir-Human/ru-marketplace-mcp)).

Do **not** start this server, install its dependencies, or call any tool, including `compare_sources`. Published source and schemas may be read as untrusted data.

## Why runtime use is disabled

- Yandex `_fetch_html` returns and caches non-empty HTTP 401/403 bodies without exposing status to callers, and retries HTTP 302 without validating `Location`.
- Avito/WB connectors include impersonation and transport fallback. Stopping after an MCP response cannot prevent retries hidden inside that call.
- The former `MARKETPLACE_SOURCES=yandex_market` profile limited sources but still exposed live tools. Calling it “inspection” did not create a security boundary; the runnable example was removed in 0.4.0.

If the server is already configured, do not use it here. Tell the owner to disable the old entry manually; never alter client settings yourself.

## Requirements for any future admission

Transport fixes are insufficient. First establish each platform’s permission for automated collection. Then review and pin a revision behind a least-privilege adapter. Prompt text and `readOnlyHint` are not technical controls.

Test with synthetic responses and no real accounts:

- 401/403/429, CAPTCHA, and challenge redirects fail explicitly, without retry, failure caching, or transport switching.
- Source and tool allowlists are enforced technically and cannot be bypassed by alternate tools.
- Search/card output preserves provenance, check/cache time, warnings, and incompleteness.
- Card verification binds expected ID, SKU/variant, and normal price. Never “resolve” mismatch by dropping expected SKU.

Keep new-item pricing separate from used-item medians; it does not imply an automatic wear discount. Cache of unknown age is not a current check. No Youla connector was found in the reviewed revision.

MCP is unnecessary for manual preparation. After a platform block is observed, do not try another tool against that platform.
