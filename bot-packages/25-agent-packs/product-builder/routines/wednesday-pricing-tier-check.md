# Routine: Wednesday Good/Better/Best pricing model (`wednesday-pricing-tier-check`)

- **Agent:** AgentScout Product Builder Agent (`product-builder`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/pricing-and-mvp-scope/SKILL.md`
- **Helper Script:** `scripts/model_product_pricing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/model_product_pricing.py to stress-test unit costs, target margins, and tier boundaries for {{YOUR_COMPANY}}.

1. Load `context/business-profile.md` and `skills/pricing-and-mvp-scope/SKILL.md`.
2. Run `python3 scripts/model_product_pricing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
