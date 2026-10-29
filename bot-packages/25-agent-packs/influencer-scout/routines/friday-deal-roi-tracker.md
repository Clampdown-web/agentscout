---
id: friday-deal-roi-tracker
title: "Friday creator brief & forecasted ROI check"
cron: "0 14 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/calculate_creator_roi.py"
skill: "skills/creator-roi/SKILL.md"
---

# Routine: Friday creator brief & forecasted ROI check (`friday-deal-roi-tracker`)

- **Schedule:** `0 14 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Influencer Scout Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/calculate_creator_roi.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Prepare outreach briefs, FTC disclosure lines, and forecasted order ROI for owner-approved creators at {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/creator-roi/SKILL.md`.
2. Run `python3 scripts/calculate_creator_roi.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
