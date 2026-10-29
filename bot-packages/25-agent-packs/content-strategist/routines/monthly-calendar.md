---
id: monthly-calendar
title: "30-day calendar"
cron: "0 10 1 * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_30day_calendar.py"
skill: "skills/thirty-day-calendar/SKILL.md"
---

# Routine: 30-day calendar (`monthly-calendar`)

- **Schedule:** `0 10 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Content Strategist Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_30day_calendar.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft next month's calendar for {{YOUR_COMPANY}}. Do not publish.

1. Read `context/business-profile.md` and `skills/thirty-day-calendar/SKILL.md`.
2. Run `python3 scripts/generate_30day_calendar.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
