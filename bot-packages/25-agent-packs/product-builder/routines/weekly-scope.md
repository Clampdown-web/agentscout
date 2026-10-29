# Routine: Weekly scope review (`weekly-scope`)

- **Agent:** AgentScout Product Builder Agent (`product-builder`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/pricing-and-mvp-scope/SKILL.md`
- **Helper Script:** `scripts/model_product_pricing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Re-score the backlog for {{YOUR_COMPANY}} and name anything that snuck into the MVP.

1. Load `context/business-profile.md` and `skills/pricing-and-mvp-scope/SKILL.md`.
2. Run `python3 scripts/model_product_pricing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
