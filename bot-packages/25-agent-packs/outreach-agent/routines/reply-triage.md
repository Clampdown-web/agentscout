---
id: reply-triage
title: "Reply intent pass"
cron: "0 13,17 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/lint_outreach_sequence.py"
skill: "skills/cold-email-sequence/SKILL.md"
---

# Routine: Reply intent pass (`reply-triage`)

- **Schedule:** `0 13,17 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Outreach Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/lint_outreach_sequence.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Classify replies as interested, not now, out of office, or unsubscribe. Draft responses. Do not send.

1. Read `context/business-profile.md` and `skills/cold-email-sequence/SKILL.md`.
2. Run `python3 scripts/lint_outreach_sequence.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
