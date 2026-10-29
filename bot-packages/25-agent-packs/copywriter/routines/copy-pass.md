# Routine: Midweek copy pass (`copy-pass`)

- **Agent:** AgentScout Copywriter Agent (`copywriter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/conversion-copy-audit/SKILL.md`
- **Helper Script:** `scripts/audit_sales_copy.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Audit the live hero and one email for {{YOUR_COMPANY}}. Return a revised draft and the score. Do not publish.

1. Load `context/business-profile.md` and `skills/conversion-copy-audit/SKILL.md`.
2. Run `python3 scripts/audit_sales_copy.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
