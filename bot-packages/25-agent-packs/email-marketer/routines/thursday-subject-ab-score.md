# Routine: Thursday subject & preview A/B check (`thursday-subject-ab-score`)

- **Agent:** AgentScout Email Marketer Agent (`email-marketer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/newsletter-issue-score/SKILL.md`
- **Helper Script:** `scripts/score_newsletter_issue.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Score subject pairs, plain-text twin links, and unsubscribe headers for {{YOUR_COMPANY}} with scripts/score_newsletter_issue.py.

1. Load `context/business-profile.md` and `skills/newsletter-issue-score/SKILL.md`.
2. Run `python3 scripts/score_newsletter_issue.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
