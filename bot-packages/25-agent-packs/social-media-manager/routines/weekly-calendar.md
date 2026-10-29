---
id: weekly-calendar
title: "Next week's calendar"
cron: "0 11 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_social_hooks.py"
skill: "skills/social-hook-desk/SKILL.md"
---

# Routine: Next week's calendar (`weekly-calendar`)

- **Schedule:** `0 11 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Social Media Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_social_hooks.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Propose five posts across the pillars. Leave them in draft.

1. Read `context/business-profile.md` and `skills/social-hook-desk/SKILL.md`.
2. Run `python3 scripts/score_social_hooks.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
