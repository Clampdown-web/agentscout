---
id: friday-objection-refresh
title: "Friday customer objection refresh"
cron: "0 14 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/audit_sales_copy.py"
skill: "skills/conversion-copy-audit/SKILL.md"
---

# Routine: Friday customer objection refresh (`friday-objection-refresh`)

- **Schedule:** `0 14 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Copywriter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/audit_sales_copy.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Turn this week's sales and support questions for {{YOUR_COMPANY}} into FAQ and objection-handling copy drafts.

1. Read `context/business-profile.md` and `skills/conversion-copy-audit/SKILL.md`.
2. Run `python3 scripts/audit_sales_copy.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
