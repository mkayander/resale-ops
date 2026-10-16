# Evidence-based pricing

Source access is governed by the [platform registry](platforms.md). **Account-linked** marketplace automation (login, forms, feeds, owner session MCP) still requires an admitted adapter. **Public research**—general web search and anonymous unauthenticated views of public pages—is allowed in `prepare_only` for estimates and does not require a marketplace read adapter.

Use two tiers. Report which tier drives each number.

## Tier A — market estimate (usually sufficient)

Purpose: a practical asking-price range for a used item when super-precise, card-by-card marketplace verification is unnecessary.

Allowed inputs:

- Internet search snippets and result pages (aggregators, reviews, forums, retailer used/refurb prices where shown).
- Anonymous public views of marketplace **search or listing pages** without logging into the owner’s account, at low volume, stopping on blocks.
- Owner-supplied screenshots or copy, labeled honestly.

Method:

1. Build queries from confirmed brand/model/variant, starting in the user’s city when relevant. Record date, region, and query.
2. Collect **price signals** (not necessarily full comparable cards): asking prices, “from” ranges, completed-sale hints if clearly labeled as such, and new-price anchors for context only.
3. Label each signal `web_public`, `user_provided`, or `user_verified` with URL or attribution and `checked_at` when known.
4. Separate used private sales from new goods, services, parts, rentals, and wholesale. Deduplicate obvious duplicates without evading platform controls.
5. Produce an **estimated asking range** and a rounded **market reference** with explicit limitations: sample may be stale, mixed geography, mixed condition, or thin. Prefer wide ranges and low confidence over false precision. For thin samples, state that the figure is indicative only.

Tier A is enough to propose market reference and quick-sale prices for most resale tasks. Do not present Tier A as a verified “current median” of live homogeneous listings unless you also satisfy Tier B.

## Tier B — verified comparables (optional, higher confidence)

Use when the owner needs stricter evidence, large-value items, or disputed pricing—or when Tier A is too thin.

In addition to Tier A tools, the owner may open listing cards and supply direct URL, price, attributes, city, condition, bundle, availability, and check time. With an admitted read adapter, the agent may verify cards directly.

For each comparable record:

- direct URL;
- `checked_at` as ISO 8601 with timezone, only when known;
- RUB asking price, model/variant, condition, bundle, city;
- `available | removed | unknown`;
- `user_provided | user_verified | agent_verified` plus evidence;
- `included: true | false` and reason.

A URL or snippet alone is not verification. `user_verified` requires owner-confirmed current price, availability, attributes, and check time. `agent_verified` requires observation through an admitted method. Do not retain seller names, phone numbers, or full copied descriptions.

Compute the median asking price only from a verified homogeneous sample: available cards with known check time and sufficient attributes. Exclude unverified `user_provided` data from the median. With zero qualifying observations, there is no Tier B median; fall back to Tier A or a research plan.

For `n >= 5` in Tier B, an explicitly described IQR is acceptable; below five, use min/max and low confidence.

## Adjustments and quick sale

Market reference = rounded central tendency (Tier B median, or Tier A estimate). Ground bundle/defect adjustments in specific comparables or label them explicitly as expert judgment.

Quick-sale price = lower part of the comparable or estimated range. A 10–20% reduction may be offered as a working hypothesis, not an empirically proven sale-time guarantee. State the final number and basis.

Never claim an item sold at its asking price. Check time is not publication time. After a block on a platform, mark platform-specific evidence stale and do not retry that access path.
