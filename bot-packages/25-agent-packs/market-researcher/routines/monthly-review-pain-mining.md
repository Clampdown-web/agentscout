---
id: monthly-review-pain-mining
title: "Monthly competitor review & launch digest"
cron: "0 10 1 * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/competitor_diff_check.py"
skill: "skills/competitor-diff/SKILL.md"
---

# Routine: Monthly competitor review & launch digest (`monthly-review-pain-mining`)

- **Schedule:** `0 10 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Market Researcher Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/competitor_diff_check.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Summarize dated customer complaints and product launches across tracked competitors for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/competitor-diff/SKILL.md`.
2. Run `python3 scripts/competitor_diff_check.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
