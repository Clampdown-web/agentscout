# Routine: Weekly creator shortlist (`weekly-shortlist`)

- **Agent:** AgentScout Influencer Scout Agent (`influencer-scout`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/creator-roi/SKILL.md`
- **Helper Script:** `scripts/calculate_creator_roi.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Score the creator sheet for {{YOUR_COMPANY}}. Do not email creators.

1. Load `context/business-profile.md` and `skills/creator-roi/SKILL.md`.
2. Run `python3 scripts/calculate_creator_roi.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
