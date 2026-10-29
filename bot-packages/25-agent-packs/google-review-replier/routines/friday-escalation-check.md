---
id: friday-escalation-check
title: "Weekly P0 complaint & SLA check"
cron: "0 15 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_review_replies.py"
skill: "skills/review-reply-desk/SKILL.md"
---

# Routine: Weekly P0 complaint & SLA check (`friday-escalation-check`)

- **Schedule:** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Google Review Replier Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_review_replies.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Verify every 1-star and 2-star review for {{YOUR_COMPANY}} has an owner-reviewed recovery draft and offline support handoff.

1. Read `context/business-profile.md` and `skills/review-reply-desk/SKILL.md`.
2. Run `python3 scripts/generate_review_replies.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
