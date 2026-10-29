---
id: weekly-headline-variants
title: "Monday headline & hook variants"
cron: "0 9 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/audit_sales_copy.py"
skill: "skills/conversion-copy-audit/SKILL.md"
---

# Routine: Monday headline & hook variants (`weekly-headline-variants`)

- **Schedule:** `0 9 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Copywriter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/audit_sales_copy.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft three hypothesis-backed headline and CTA variants for {{YOUR_COMPANY}} and score them with scripts/audit_sales_copy.py. Do not publish.

1. Read `context/business-profile.md` and `skills/conversion-copy-audit/SKILL.md`.
2. Run `python3 scripts/audit_sales_copy.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
