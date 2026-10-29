---
id: friday-repurpose-cuts
title: "Friday long-to-short cut batch"
cron: "0 14 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/format_captions_and_cuts.py"
skill: "skills/shortform-cut-captions/SKILL.md"
---

# Routine: Friday long-to-short cut batch (`friday-repurpose-cuts`)

- **Schedule:** `0 14 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Video Editor Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/format_captions_and_cuts.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Extract top 3 short-form clip timestamps and SRT captions from this week's long video for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/shortform-cut-captions/SKILL.md`.
2. Run `python3 scripts/format_captions_and_cuts.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
