# Routine: Friday customer objection refresh (`friday-objection-refresh`)

- **Agent:** AgentScout Copywriter Agent (`copywriter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 14 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/conversion-copy-audit/SKILL.md`
- **Helper Script:** `scripts/audit_sales_copy.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Turn this week's sales and support questions for {{YOUR_COMPANY}} into FAQ and objection-handling copy drafts.

1. Load `context/business-profile.md` and `skills/conversion-copy-audit/SKILL.md`.
2. Run `python3 scripts/audit_sales_copy.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
