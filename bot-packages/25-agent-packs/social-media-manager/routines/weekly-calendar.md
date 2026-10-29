# Routine: Next week's calendar (`weekly-calendar`)

- **Agent:** AgentScout Social Media Manager Agent (`social-media-manager`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/social-hook-desk/SKILL.md`
- **Helper Script:** `scripts/score_social_hooks.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Propose five posts across the pillars. Leave them in draft.

1. Load `context/business-profile.md` and `skills/social-hook-desk/SKILL.md`.
2. Run `python3 scripts/score_social_hooks.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
