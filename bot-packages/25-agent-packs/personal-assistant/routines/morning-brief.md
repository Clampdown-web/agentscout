---
id: morning-brief
title: "Morning briefing"
cron: "0 7 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/daily_exec_briefing.py"
skill: "skills/daily-exec-briefing/SKILL.md"
---

# Routine: Morning briefing (`morning-brief`)

- **Schedule:** `0 7 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Personal Assistant Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/daily_exec_briefing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Write the morning brief for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}. Do not delete or send mail.

1. Read `context/business-profile.md` and `skills/daily-exec-briefing/SKILL.md`.
2. Run `python3 scripts/daily_exec_briefing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
