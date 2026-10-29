---
id: daily-community
title: "Daily community draft"
cron: "0 10 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/community_health_score.py"
skill: "skills/community-health/SKILL.md"
---

# Routine: Daily community draft (`daily-community`)

- **Schedule:** `0 10 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Community Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/community_health_score.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Score health and draft one prompt for {{YOUR_COMPANY}}. Do not post or ban.

1. Read `context/business-profile.md` and `skills/community-health/SKILL.md`.
2. Run `python3 scripts/community_health_score.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
