# Resale Ops: web ChatGPT Project setup

Set up Resale Ops for the current user in a web ChatGPT Project. Follow these steps in order and never claim that a resource was created or connected until you verify it by reading it back. Communicate with the user in the language they prefer, and generate copyable blocks in that language. Codex, Claude Code, and Cursor are optional alternative clients; do not send the user through their installation flow for the ChatGPT Project setup.

## Setup sequence

1. Check that the user is working inside a dedicated ChatGPT Project. If there is no project, or this chat is outside one, explain why the project is needed and ask the user to create it and continue there. Do not create a project silently.
2. Read the current skill from the configured GitHub source before doing work. If the project instructions or private locations file records a source commit, compare it with the current `main` commit when GitHub metadata is available. If it changed, briefly summarize the relevant update, use the newly read skill in this chat, and offer to refresh the project instructions or uploaded snapshot. If no commit is recorded, report that this is the baseline and include the current commit in the setup block. Do not silently replace a pinned snapshot. If the comparison is unavailable, say so; do not claim that the source is current.
3. Check whether Google Drive and Google Sheets are connected with the read and write capabilities required for this workflow. If not, ask the user to connect them in the app settings and continue after that.
4. In Google Drive, look inside the verified `Resale` folder for the private file `.resale-locations.json` and for existing folders or spreadsheets. Reuse verified resources first; if there are multiple candidates, show them and ask the user to choose.
5. If the resources do not exist, create a private `Resale` folder, its `queue` subfolder, and a `Resale Queue` spreadsheet with a `Queue` tab and these headers:

   `id, status, title, city, list_price_rub, quick_sale_rub, metadata_status, post_photo_count, prepared_at, updated_at, folder_name, folder_url, notes`

6. Create or update the private Drive file `.resale-locations.json` inside the `Resale` folder with the actual IDs and URLs. Read it back, and never put these private values in the public repository or local source files.
7. Determine whether Resale Ops instructions are already saved in Project Instructions. If the host cannot expose the project instructions, ask the user to confirm or paste the current block; do not assume that it is absent.
8. If the city is unknown, ask only for the city. After the answer, if the block is missing or outdated, provide one complete copyable block using the actual links and IDs from step 6, the `Queue` tab, the city, and the chosen platforms (default: Avito and Youla). Ask the user to paste it into Project Instructions and confirm that it was saved; do not call setup complete until they confirm.
9. After the instructions are saved, ask whether the user wants to create the first item now. Only after the user names the item or explicitly confirms should you create a unique item folder with `inbox` and `photos/post`, then `listing.md` and `meta.json`. Show the `inbox` link for photo upload.

## Project instructions block

Use this template after replacing every placeholder with verified values. Generate the final block in the user's preferred language.

```text
Use Resale Ops to prepare listings for items I want to sell.
Before working, read the skill:
https://raw.githubusercontent.com/mkayander/resale-ops/main/skills/resale-ops/SKILL.md
Open any required reference files from the same GitHub folder.
Source commit recorded at setup: <commit SHA>
At the start of each new chat, check whether the GitHub source has changed since
the recorded source commit. If it changed, use the newly read skill and offer a
replacement for these project instructions; do not silently replace a pinned snapshot.
In a long-lived chat, repeat this check after a long pause, before a new setup or
integration workflow, or when I ask about updates or behavior that may have changed.
Do not perform the check on every routine item message.

Google Drive stores photos and listing materials. Google Sheets stores the queue.
Resale folder: <verified URL and ID>
Queue folder: <verified URL and ID>
Google Sheets file: <verified URL and ID>
Tab: Queue
City: <city>
Platforms: Avito and Youla.

Check existing resources and update the item row by its ID.
Ask important questions, propose regular and quick-sale prices, prepare platform-specific
copy and photos according to the skill, save materials in Drive, and update Queue.
I publish listings manually. Respond in the language of my message.
```

If project instructions already contain Resale Ops, do not duplicate them. Check the actual IDs and offer a replacement only when they differ. If the user has not confirmed saving a new block, do not call setup complete.

## After setup

After the user creates the first item, ask them to upload photos of that one item to `inbox`. Then follow the skill: identify the model and condition, ask consequential questions, research specifications and prices, prepare separate Avito and Youla copy, inspect the photos, and update `listing.md`, `meta.json`, and the matching Queue row.

Marketplace account work and publication are forbidden by default. A direct user
authorization must name the specific item, platform and unchanged final listing
version; a general request to sell, prepare or fill a draft is not publication
approval. Use Chrome DevTools MCP only for an already admitted browser method.
The user completes login, CAPTCHA, 2FA and identity checks manually. Paid actions,
moderation submission, import and feed upload require separate direct approval.
