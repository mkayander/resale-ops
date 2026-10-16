# Agents working in this repository

## Cloud Agents (Cursor)

This repo is set up for **resale-ops** with a persistent cloud queue.

1. **Project rules** — `.cursor/rules/resale-ops.mdc` (Drive + Sheets IDs; applied on every run in this repo).
2. **Skill** — `skills/resale-ops/SKILL.md` (install locally per `docs/INSTALL.md` for desktop; cloud agents read from the repo).
3. **MCP** — enable **Google Drive** and **Google Sheets** on [Cloud Agents](https://cursor.com/agents) and complete OAuth.
4. **Drive anchor** — `Resale/.resale-locations.json` (same JSON as the rule file; used when rules are empty).

Optional: copy the JSON from `.cursor/rules/resale-ops.mdc` into **Cursor → Settings → Rules → User rules** if you use resale-ops from **other** repositories.

Photo tooling on cloud VMs: `pip install -r requirements-queue.txt` (or use the environment `install` in `.cursor/environment.json` when present).

## Package checks

```sh
python3 -m pip install -r requirements-dev.txt -r requirements-queue.txt
python3 scripts/check_package.py
python3 -m unittest discover -s tests -v
```
