---
id: thursday-subject-ab-score
title: "Thursday subject & preview A/B check"
cron: "0 11 * * 4"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_newsletter_issue.py"
skill: "skills/newsletter-issue-score/SKILL.md"
---

# Routine: Thursday subject & preview A/B check (`thursday-subject-ab-score`)

- **Schedule:** `0 11 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Email Marketer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_newsletter_issue.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Score subject pairs, plain-text twin links, and unsubscribe headers for {{YOUR_COMPANY}} with scripts/score_newsletter_issue.py.

1. Read `context/business-profile.md` and `skills/newsletter-issue-score/SKILL.md`.
2. Run `python3 scripts/score_newsletter_issue.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
