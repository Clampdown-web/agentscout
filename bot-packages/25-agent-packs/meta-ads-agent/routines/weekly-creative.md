# Routine: Weekly creative refresh (`weekly-creative`)

- **Agent:** AgentScout Meta Ads Agent (`meta-ads-agent`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/ad-roas-rules/SKILL.md`
- **Helper Script:** `scripts/evaluate_ad_roas.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Propose the next three concepts that are not the current hook.

1. Load `context/business-profile.md` and `skills/ad-roas-rules/SKILL.md`.
2. Run `python3 scripts/evaluate_ad_roas.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
