---
id: reminder-sweep
title: "Reminder and no-show sweep"
cron: "0 8 * * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/build_call_briefing.py"
skill: "skills/call-briefing-slots/SKILL.md"
---

# Routine: Reminder and no-show sweep (`reminder-sweep`)

- **Schedule:** `0 8 * * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Appointment Setter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/build_call_briefing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

List calls in the next 24 hours and no-shows from yesterday for {{YOUR_COMPANY}}. Draft the notes. Do not send.

1. Read `context/business-profile.md` and `skills/call-briefing-slots/SKILL.md`.
2. Run `python3 scripts/build_call_briefing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
