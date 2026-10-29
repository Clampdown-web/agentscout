---
id: monday-engagement-vetting
title: "Monday engagement & CPM anomaly check"
cron: "0 10 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/calculate_creator_roi.py"
skill: "skills/creator-roi/SKILL.md"
---

# Routine: Monday engagement & CPM anomaly check (`monday-engagement-vetting`)

- **Schedule:** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Influencer Scout Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/calculate_creator_roi.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/calculate_creator_roi.py on prospective creators for {{YOUR_COMPANY}} and flag suspect engagement rates.

1. Read `context/business-profile.md` and `skills/creator-roi/SKILL.md`.
2. Run `python3 scripts/calculate_creator_roi.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
