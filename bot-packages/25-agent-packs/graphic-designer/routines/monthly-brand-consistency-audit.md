# Routine: Monthly brand token & contrast audit (`monthly-brand-consistency-audit`)

- **Agent:** AgentScout Graphic Designer Agent (`graphic-designer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/brand-card-system/SKILL.md`
- **Helper Script:** `scripts/generate_brand_card_spec.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Audit recent visual assets and thumbnails against {{YOUR_COMPANY}} hex tokens and 4.5:1 contrast rules. Report only.

1. Load `context/business-profile.md` and `skills/brand-card-system/SKILL.md`.
2. Run `python3 scripts/generate_brand_card_spec.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
