# Routine: Daily review replies (`daily-review-drafts`)

- **Agent:** AgentScout Google Review Replier Agent (`google-review-replier`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/review-reply-desk/SKILL.md`
- **Helper Script:** `scripts/generate_review_replies.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Draft replies for new reviews of {{YOUR_COMPANY}}. Do not post them.

1. Load `context/business-profile.md` and `skills/review-reply-desk/SKILL.md`.
2. Run `python3 scripts/generate_review_replies.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
