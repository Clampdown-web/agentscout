# Routine: Weekly ledger reconcile (`weekly-reconcile`)

- **Agent:** AgentScout Accountant Agent (`accountant`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 8 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/bookkeeping-tax-prep/SKILL.md`
- **Helper Script:** `scripts/reconcile_ledger.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Reconcile last week's bank export for {{YOUR_COMPANY}}. Return matched rows, the needs-review queue, and one cash warning.

1. Load `context/business-profile.md` and `skills/bookkeeping-tax-prep/SKILL.md`.
2. Run `python3 scripts/reconcile_ledger.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
