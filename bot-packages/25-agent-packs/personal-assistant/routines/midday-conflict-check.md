---
id: midday-conflict-check
title: "Midday calendar conflict & prep check"
cron: "0 12 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/daily_exec_briefing.py"
skill: "skills/daily-exec-briefing/SKILL.md"
---

# Routine: Midday calendar conflict & prep check (`midday-conflict-check`)

- **Schedule:** `0 12 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Personal Assistant Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/daily_exec_briefing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Check afternoon holds, travel gaps, and next-day meeting prep questions for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/daily-exec-briefing/SKILL.md`.
2. Run `python3 scripts/daily_exec_briefing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
