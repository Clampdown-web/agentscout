# Routine: Monthly review themes (`monthly-themes`)

- **Agent:** AgentScout Google Review Replier Agent (`google-review-replier`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/review-reply-desk/SKILL.md`
- **Helper Script:** `scripts/generate_review_replies.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Summarize repeated themes and the response time. No public posts.

1. Load `context/business-profile.md` and `skills/review-reply-desk/SKILL.md`.
2. Run `python3 scripts/generate_review_replies.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
