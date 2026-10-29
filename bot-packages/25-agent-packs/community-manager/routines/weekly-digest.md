# Routine: Weekly engagement digest (`weekly-digest`)

- **Agent:** AgentScout Community Manager Agent (`community-manager`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/community-health/SKILL.md`
- **Helper Script:** `scripts/community_health_score.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Summarize active rate, quiet new members, and FAQ gaps.

1. Load `context/business-profile.md` and `skills/community-health/SKILL.md`.
2. Run `python3 scripts/community_health_score.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
