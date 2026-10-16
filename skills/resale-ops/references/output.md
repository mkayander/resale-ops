# Result schema

Present compactly in the conversation language selected by `SKILL.md`:

1. **Item** — identification and confidence; separate photo evidence, owner report, inference, web_public specs, and unknowns.
2. **Condition** — defects, bundle, city, and handoff method.
3. **Platforms** — access mode and known active/pending/rejected/archived/draft records per platform. If status is unknown, say so and create nothing.
4. **Product facts** — measurements, materials, model codes, and paraphrased pros with `web_public` (or other) sources; note variant uncertainty.
5. **Price evidence** — Tier A signals and/or Tier B comparables: URL, check time, evidence label (`web_public | user_provided | user_verified | agent_verified`), price, attributes, availability, inclusion, and reason. Never invent cards or timestamps.
6. **Calculation** — tier used, `n`, range, median or estimate, exclusions, adjustments, confidence, and limitations. For admitted integrations include source/version, warnings, incompleteness, and cache age. Do not use current `ru-marketplace-mcp`. Keep new-item prices outside the used sample.
7. **Prices** — market reference, quick-sale price, and selected listing price.
8. **Listing package per platform** — title, description, candidate category, attributes, price, terms, and unresolved fields.
9. **Photos** — queue: `photos/post/` filenames/order after `prepare-photos`; optional **reference images** (URLs) in `listing.md`; visible personal data; `photos.metadata_status` from `meta.json`. Never claim EXIF removal without the prepare script run.
10. **Account** — in `prepare_only`, state that the owner’s marketplace account was not opened or changed (public web research may still have occurred). For admitted methods, report observed fields/errors without personal data.
11. **Status** — `prepared | form_filled | draft_saved | blocked | submitted | published`, with evidence source. Manual work ends at `prepared`; label later owner-reported status as such.
12. **Next step** — make the stop before publication explicit.

Exclude exact address/phone, cookies, tokens, and unrelated-tab content. Keep personal work files local and outside public repositories.
