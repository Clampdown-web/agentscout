---
id: quarterly-refresh
title: "Decay and refresh list"
cron: "0 10 1 1,4,7,10 *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_30day_calendar.py"
skill: "skills/thirty-day-calendar/SKILL.md"
---

# Routine: Decay and refresh list (`quarterly-refresh`)

- **Schedule:** `0 10 1 1,4,7,10 *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Content Strategist Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_30day_calendar.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

List URLs that should be updated before new topics are added.

1. Read `context/business-profile.md` and `skills/thirty-day-calendar/SKILL.md`.
2. Run `python3 scripts/generate_30day_calendar.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
