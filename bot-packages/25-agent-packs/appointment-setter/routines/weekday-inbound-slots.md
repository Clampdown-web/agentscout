---
id: weekday-inbound-slots
title: "Inbound lead qualification & slot prep"
cron: "0 9,14 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/build_call_briefing.py"
skill: "skills/call-briefing-slots/SKILL.md"
---

# Routine: Inbound lead qualification & slot prep (`weekday-inbound-slots`)

- **Schedule:** `0 9,14 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Appointment Setter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/build_call_briefing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Qualify new inbound inquiries for {{YOUR_COMPANY}} and build timezone-matched slot options with scripts/build_call_briefing.py.

1. Read `context/business-profile.md` and `skills/call-briefing-slots/SKILL.md`.
2. Run `python3 scripts/build_call_briefing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
