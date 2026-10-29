---
id: weekly-icp-refresh
title: "Weekly ICP refresh"
cron: "0 11 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_leads_pipeline.py"
skill: "skills/icp-lead-scoring/SKILL.md"
---

# Routine: Weekly ICP refresh (`weekly-icp-refresh`)

- **Schedule:** `0 11 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Lead Gen Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_leads_pipeline.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Compare wins and losses this week and propose one ICP edit for {{YOUR_OWNER_NAME}} to accept.

1. Read `context/business-profile.md` and `skills/icp-lead-scoring/SKILL.md`.
2. Run `python3 scripts/score_leads_pipeline.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
