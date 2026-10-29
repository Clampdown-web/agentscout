# Routine: Weekly newsletter draft (`weekly-issue`)

- **Agent:** AgentScout Email Marketer Agent (`email-marketer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/newsletter-issue-score/SKILL.md`
- **Helper Script:** `scripts/score_newsletter_issue.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Draft and score this week's issue for {{YOUR_COMPANY}}. Do not schedule it.

1. Load `context/business-profile.md` and `skills/newsletter-issue-score/SKILL.md`.
2. Run `python3 scripts/score_newsletter_issue.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
