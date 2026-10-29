---
id: daily-review-drafts
title: "Daily review replies"
cron: "0 9 * * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_review_replies.py"
skill: "skills/review-reply-desk/SKILL.md"
---

# Routine: Daily review replies (`daily-review-drafts`)

- **Schedule:** `0 9 * * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Google Review Replier Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_review_replies.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft replies for new reviews of {{YOUR_COMPANY}}. Do not post them.

1. Read `context/business-profile.md` and `skills/review-reply-desk/SKILL.md`.
2. Run `python3 scripts/generate_review_replies.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
