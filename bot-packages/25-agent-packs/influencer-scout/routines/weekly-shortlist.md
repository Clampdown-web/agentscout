---
id: weekly-shortlist
title: "Weekly creator shortlist"
cron: "0 10 * * 3"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/calculate_creator_roi.py"
skill: "skills/creator-roi/SKILL.md"
---

# Routine: Weekly creator shortlist (`weekly-shortlist`)

- **Schedule:** `0 10 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Influencer Scout Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/calculate_creator_roi.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Score the creator sheet for {{YOUR_COMPANY}}. Do not email creators.

1. Read `context/business-profile.md` and `skills/creator-roi/SKILL.md`.
2. Run `python3 scripts/calculate_creator_roi.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
