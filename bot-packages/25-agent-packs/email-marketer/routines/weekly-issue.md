---
id: weekly-issue
title: "Weekly newsletter draft"
cron: "0 9 * * 2"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_newsletter_issue.py"
skill: "skills/newsletter-issue-score/SKILL.md"
---

# Routine: Weekly newsletter draft (`weekly-issue`)

- **Schedule:** `0 9 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Email Marketer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_newsletter_issue.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft and score this week's issue for {{YOUR_COMPANY}}. Do not schedule it.

1. Read `context/business-profile.md` and `skills/newsletter-issue-score/SKILL.md`.
2. Run `python3 scripts/score_newsletter_issue.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
