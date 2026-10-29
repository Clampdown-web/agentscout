# Routine: Candidate pipeline nudge (`daily-pipeline`)

- **Agent:** AgentScout Recruiter Agent (`recruiter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `30 9 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/candidate-rubric/SKILL.md`
- **Helper Script:** `scripts/score_candidate_rubric.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

List candidates with no touch in three business days. Draft the next note. Do not send.

1. Load `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
