# Routine: Monday engagement & CPM anomaly check (`monday-engagement-vetting`)

- **Agent:** AgentScout Influencer Scout Agent (`influencer-scout`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/creator-roi/SKILL.md`
- **Helper Script:** `scripts/calculate_creator_roi.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/calculate_creator_roi.py on prospective creators for {{YOUR_COMPANY}} and flag suspect engagement rates.

1. Load `context/business-profile.md` and `skills/creator-roi/SKILL.md`.
2. Run `python3 scripts/calculate_creator_roi.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
