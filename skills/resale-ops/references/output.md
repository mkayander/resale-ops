# Result schema

Present compactly in the user’s language:

1. **Item** — identification and confidence; separate photo evidence, owner report, inference, and unknowns.
2. **Condition** — defects, bundle, city, and handoff method.
3. **Platforms** — access mode and known active/pending/rejected/archived/draft records per platform. If status is unknown, say so and create nothing.
4. **Comparables** — direct URL, check time and evidence label (`user_provided | user_verified | agent_verified`), price, relevant attributes, availability, inclusion decision, and reason. Never invent cards or timestamps to fill the schema.
5. **Calculation** — `n`, median, range, exclusions, adjustments, and limitations. For any future admitted integration include source/version, warnings, incompleteness, cache age, and direct-card verification. Do not use current `ru-marketplace-mcp`. Keep new-item prices outside the used sample.
6. **Prices** — market reference, quick-sale price, and selected listing price.
7. **Listing package per platform** — title, description, candidate category, attributes, price, terms, and unresolved fields.
8. **Photos** — real selected filenames/order, visible personal data, metadata-inspection status, and prepared-copy status. Never claim EXIF removal without verification.
9. **Account** — in `prepare_only`, state in the user’s language that it was not opened or changed. For admitted methods, report observed fields/errors and save evidence without personal data.
10. **Status** — `prepared | form_filled | draft_saved | blocked | submitted | published`, with evidence source. Manual work ends at `prepared`; label later owner-reported status as such.
11. **Next step** — make the stop before publication explicit.

Exclude exact address/phone, cookies, tokens, and unrelated-tab content. Keep personal work files outside public repositories.
