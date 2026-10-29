---
id: daily-hooks
title: "Daily hook score"
cron: "0 8 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_social_hooks.py"
skill: "skills/social-hook-desk/SKILL.md"
---

# Routine: Daily hook score (`daily-hooks`)

- **Schedule:** `0 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Social Media Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_social_hooks.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Score today's hooks for {{YOUR_COMPANY}} and format the winner. Do not post.

1. Read `context/business-profile.md` and `skills/social-hook-desk/SKILL.md`.
2. Run `python3 scripts/score_social_hooks.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
