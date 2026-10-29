# Routine: Daily qualified lead batch (`daily-lead-batch`)

- **Agent:** AgentScout Lead Gen Agent (`lead-gen`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/icp-lead-scoring/SKILL.md`
- **Helper Script:** `scripts/score_leads_pipeline.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Score today's prospect file for {{YOUR_COMPANY}}. Cap the qualified list. Do not email anyone.

1. Load `context/business-profile.md` and `skills/icp-lead-scoring/SKILL.md`.
2. Run `python3 scripts/score_leads_pipeline.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
