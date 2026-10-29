---
id: month-close
title: "Month-end close pack"
cron: "0 9 1 * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/reconcile_ledger.py"
skill: "skills/bookkeeping-tax-prep/SKILL.md"
---

# Routine: Month-end close pack (`month-close`)

- **Schedule:** `0 9 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Accountant Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/reconcile_ledger.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft the month-end close checklist: accruals, prepaids, unmatched cash, and questions for the tax professional. Do not file anything.

1. Read `context/business-profile.md` and `skills/bookkeeping-tax-prep/SKILL.md`.
2. Run `python3 scripts/reconcile_ledger.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
