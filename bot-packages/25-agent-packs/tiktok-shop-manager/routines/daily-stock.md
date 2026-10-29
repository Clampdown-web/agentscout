# Routine: Inventory alert check (`daily-stock`)

- **Agent:** AgentScout TikTok Shop Manager Agent (`tiktok-shop-manager`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/shop-listing-optimizer/SKILL.md`
- **Helper Script:** `scripts/optimize_shop_listing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Check listing stock against the reorder point for {{YOUR_COMPANY}}. Do not change the live listing.

1. Load `context/business-profile.md` and `skills/shop-listing-optimizer/SKILL.md`.
2. Run `python3 scripts/optimize_shop_listing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
