---
id: weekly-deliverability-lint
title: "Weekly sequence & spam-word lint"
cron: "0 10 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/lint_outreach_sequence.py"
skill: "skills/cold-email-sequence/SKILL.md"
---

# Routine: Weekly sequence & spam-word lint (`weekly-deliverability-lint`)

- **Schedule:** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Outreach Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/lint_outreach_sequence.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Lint all active outreach templates for {{YOUR_COMPANY}} with scripts/lint_outreach_sequence.py and verify unsubscribe/footer readiness.

1. Read `context/business-profile.md` and `skills/cold-email-sequence/SKILL.md`.
2. Run `python3 scripts/lint_outreach_sequence.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
