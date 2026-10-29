---
id: thursday-pricing-battlecard-check
title: "Thursday pricing & feature matrix check"
cron: "0 11 * * 4"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/competitor_diff_check.py"
skill: "skills/competitor-diff/SKILL.md"
---

# Routine: Thursday pricing & feature matrix check (`thursday-pricing-battlecard-check`)

- **Schedule:** `0 11 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Market Researcher Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/competitor_diff_check.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/competitor_diff_check.py on saved competitor snapshots for {{YOUR_COMPANY}} and verify every claim has a dated URL.

1. Read `context/business-profile.md` and `skills/competitor-diff/SKILL.md`.
2. Run `python3 scripts/competitor_diff_check.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
