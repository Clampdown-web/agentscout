# Routine: Weekly P0 complaint & SLA check (`friday-escalation-check`)

- **Agent:** AgentScout Google Review Replier Agent (`google-review-replier`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/review-reply-desk/SKILL.md`
- **Helper Script:** `scripts/generate_review_replies.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Verify every 1-star and 2-star review for {{YOUR_COMPANY}} has an owner-reviewed recovery draft and offline support handoff.

1. Load `context/business-profile.md` and `skills/review-reply-desk/SKILL.md`.
2. Run `python3 scripts/generate_review_replies.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
