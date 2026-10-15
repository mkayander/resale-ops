# Evidence-based pricing

Source access is governed by the [platform registry](platforms.md). In manual mode, the user checks listing cards and the agent analyzes supplied data. Do not open a marketplace to apply this method without an admitted read adapter.

1. Build queries from confirmed brand/model/variant, starting in the user’s city. Record date, region, and query. Explain shipping-market differences before widening geography.
2. For each comparable record:
   - direct URL;
   - `checked_at` as ISO 8601 with timezone, only when known;
   - RUB asking price, model/variant, condition, bundle, city;
   - `available | removed | unknown`;
   - `user_provided | user_verified | agent_verified` plus evidence;
   - `included: true | false` and reason.

   A URL or snippet alone is not verification. `user_verified` requires owner-confirmed current price, availability, attributes, and check time; never call it the agent’s check. Do not retain seller names, phone numbers, or full copied descriptions.
3. Separate private used goods from new goods, repair services, parts, rentals, swaps, wholesale prices, and stores. Deduplicate the same item by ID/photo/seller without evading account controls. Exclude outliers for stated comparability reasons, never to force a desired price. Exclude zero and “from” prices.
4. Compute the median asking price only from a verified homogeneous sample: available cards with known check time and sufficient attributes. Exclude unverified `user_provided` data. Attribute owner-verified research to the owner. With zero qualifying observations, there is no current median or current market price. Report `n` and range. For `n >= 5`, an explicitly described IQR is acceptable; below five, use min/max and low confidence. Avoid false precision.
5. Market reference = rounded median comparable asking price. Ground bundle/defect adjustments in specific comparables or label them explicitly as expert judgment.
6. Quick-sale price = lower part of the comparable range. A 10–20% reduction may be offered as a working hypothesis, not an empirically proven sale-time guarantee. State the final number and basis. With weak evidence, propose a trial price and response-based review.

Never claim an item sold at its asking price. Check time is not publication time. List archived/unverified sources separately. If posting on another day, ask the owner to recheck availability and prices; only an admitted adapter may automate rechecking. After a block, mark evidence stale and do not retry access.
