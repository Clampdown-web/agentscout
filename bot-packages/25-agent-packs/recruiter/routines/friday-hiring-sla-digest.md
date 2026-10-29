# Routine: Friday hiring stage SLA digest (`friday-hiring-sla-digest`)

- **Agent:** AgentScout Recruiter Agent (`recruiter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/candidate-rubric/SKILL.md`
- **Helper Script:** `scripts/score_candidate_rubric.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Summarize candidate counts by stage, days-in-stage SLA breaches, and interview prep kits for {{YOUR_COMPANY}}.

1. Load `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
