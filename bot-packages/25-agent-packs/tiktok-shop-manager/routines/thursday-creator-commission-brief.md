# Routine: Thursday affiliate script & commission check (`thursday-creator-commission-brief`)

- **Agent:** AgentScout TikTok Shop Manager Agent (`tiktok-shop-manager`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 13 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/shop-listing-optimizer/SKILL.md`
- **Helper Script:** `scripts/optimize_shop_listing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/optimize_shop_listing.py to model creator affiliate commissions and 15-second shoppable video briefs for {{YOUR_COMPANY}}.

1. Load `context/business-profile.md` and `skills/shop-listing-optimizer/SKILL.md`.
2. Run `python3 scripts/optimize_shop_listing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
