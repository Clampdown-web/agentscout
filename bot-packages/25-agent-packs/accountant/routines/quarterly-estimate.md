---
id: quarterly-estimate
title: "Quarterly estimate reminder"
cron: "0 9 1 1,4,7,10 *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/reconcile_ledger.py"
skill: "skills/bookkeeping-tax-prep/SKILL.md"
---

# Routine: Quarterly estimate reminder (`quarterly-estimate`)

- **Schedule:** `0 9 1 1,4,7,10 *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Accountant Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/reconcile_ledger.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Prepare the quarterly estimate question list and remind {{YOUR_OWNER_NAME}} this is bookkeeping support, not a filed return.

1. Read `context/business-profile.md` and `skills/bookkeeping-tax-prep/SKILL.md`.
2. Run `python3 scripts/reconcile_ledger.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
