---
id: daily-sla-escalation-sweep
title: "Morning P0 & refund SLA sweep"
cron: "0 9 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/triage_support_tickets.py"
skill: "skills/support-ticket-triage/SKILL.md"
---

# Routine: Morning P0 & refund SLA sweep (`daily-sla-escalation-sweep`)

- **Schedule:** `0 9 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Customer Support Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/triage_support_tickets.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Surface open P0 safety/legal tickets and pending refund requests for {{YOUR_COMPANY}} for owner approval.

1. Read `context/business-profile.md` and `skills/support-ticket-triage/SKILL.md`.
2. Run `python3 scripts/triage_support_tickets.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
