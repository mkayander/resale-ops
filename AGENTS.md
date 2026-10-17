# Agents working in this repository

## resale-ops (portable skill)

- Skill: `skills/resale-ops/SKILL.md`
- **Personal queue IDs** do not belong in this repo. Store them in:
  - Cursor **User rules** or a **gitignored** `.cursor/rules/resale-ops.mdc` (see `templates/cursor-rules/resale-ops.mdc`)
  - Cloud: `Resale/.resale-locations.json` on your Drive (read via MCP)
  - Optional: `resale-locations.json` or `~/.config/resale-ops/locations.json` (gitignored)

## Cloud Agents

1. Enable **Google Drive** and **Google Sheets** MCP on [cursor.com/agents](https://cursor.com/agents) (OAuth).
2. Read locations per `skills/resale-ops/references/locations.md`.
3. `.cursor/environment.json` installs `requirements-queue.txt` for photo sanitization on the VM.

## Package checks

```sh
python3 -m pip install -r requirements-dev.txt -r requirements-queue.txt
python3 scripts/check_package.py
python3 -m unittest discover -s tests -v
```
