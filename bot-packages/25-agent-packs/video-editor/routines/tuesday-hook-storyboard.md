---
id: tuesday-hook-storyboard
title: "Tuesday 3-second hook storyboard"
cron: "0 11 * * 2"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/format_captions_and_cuts.py"
skill: "skills/shortform-cut-captions/SKILL.md"
---

# Routine: Tuesday 3-second hook storyboard (`tuesday-hook-storyboard`)

- **Schedule:** `0 11 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Video Editor Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/format_captions_and_cuts.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Audit the opening 3 seconds of upcoming recordings for {{YOUR_COMPANY}} and draft 9:16 cut lists. Draft only.

1. Read `context/business-profile.md` and `skills/shortform-cut-captions/SKILL.md`.
2. Run `python3 scripts/format_captions_and_cuts.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
