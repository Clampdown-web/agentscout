---
id: monthly-hygiene
title: "List hygiene note"
cron: "0 9 1 * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_newsletter_issue.py"
skill: "skills/newsletter-issue-score/SKILL.md"
---

# Routine: List hygiene note (`monthly-hygiene`)

- **Schedule:** `0 9 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Email Marketer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_newsletter_issue.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

List subscribers quiet for 90 days and propose a sunset. Do not delete them yourself.

1. Read `context/business-profile.md` and `skills/newsletter-issue-score/SKILL.md`.
2. Run `python3 scripts/score_newsletter_issue.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
