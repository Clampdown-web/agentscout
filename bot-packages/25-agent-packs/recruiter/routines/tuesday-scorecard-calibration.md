# Routine: Tuesday rubric & scorecard audit (`tuesday-scorecard-calibration`)

- **Agent:** AgentScout Recruiter Agent (`recruiter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/candidate-rubric/SKILL.md`
- **Helper Script:** `scripts/score_candidate_rubric.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/score_candidate_rubric.py on new applicants for {{YOUR_COMPANY}} and flag any protected-trait notes for human review.

1. Load `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
