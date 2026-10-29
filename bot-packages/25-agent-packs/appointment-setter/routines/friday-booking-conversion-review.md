---
id: friday-booking-conversion-review
title: "Weekly show-rate & briefing review"
cron: "0 16 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/build_call_briefing.py"
skill: "skills/call-briefing-slots/SKILL.md"
---

# Routine: Weekly show-rate & briefing review (`friday-booking-conversion-review`)

- **Schedule:** `0 16 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Appointment Setter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/build_call_briefing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Summarize booked calls, show rate, and reschedule follow-ups for {{YOUR_COMPANY}}. Draft only.

1. Read `context/business-profile.md` and `skills/call-briefing-slots/SKILL.md`.
2. Run `python3 scripts/build_call_briefing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
