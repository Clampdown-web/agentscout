---
id: weekly-gaps
title: "Weekly knowledge gaps"
cron: "0 16 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/triage_support_tickets.py"
skill: "skills/support-ticket-triage/SKILL.md"
---

# Routine: Weekly knowledge gaps (`weekly-gaps`)

- **Schedule:** `0 16 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Customer Support Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/triage_support_tickets.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

List the questions that had no article and propose the titles.

1. Read `context/business-profile.md` and `skills/support-ticket-triage/SKILL.md`.
2. Run `python3 scripts/triage_support_tickets.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
