# Routine: Month-end close pack (`month-close`)

- **Agent:** AgentScout Accountant Agent (`accountant`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/bookkeeping-tax-prep/SKILL.md`
- **Helper Script:** `scripts/reconcile_ledger.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Draft the month-end close checklist: accruals, prepaids, unmatched cash, and questions for the tax professional. Do not file anything.

1. Load `context/business-profile.md` and `skills/bookkeeping-tax-prep/SKILL.md`.
2. Run `python3 scripts/reconcile_ledger.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
