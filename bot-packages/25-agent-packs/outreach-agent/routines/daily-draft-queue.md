---
id: daily-draft-queue
title: "Daily outreach drafts"
cron: "30 8 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/lint_outreach_sequence.py"
skill: "skills/cold-email-sequence/SKILL.md"
---

# Routine: Daily outreach drafts (`daily-draft-queue`)

- **Schedule:** `30 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Outreach Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/lint_outreach_sequence.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft today's approved batch for {{YOUR_COMPANY}} and lint it. Leave it unsent.

1. Read `context/business-profile.md` and `skills/cold-email-sequence/SKILL.md`.
2. Run `python3 scripts/lint_outreach_sequence.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
