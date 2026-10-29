---
id: daily-lead-batch
title: "Daily qualified lead batch"
cron: "0 8 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_leads_pipeline.py"
skill: "skills/icp-lead-scoring/SKILL.md"
---

# Routine: Daily qualified lead batch (`daily-lead-batch`)

- **Schedule:** `0 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Lead Gen Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_leads_pipeline.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Score today's prospect file for {{YOUR_COMPANY}}. Cap the qualified list. Do not email anyone.

1. Read `context/business-profile.md` and `skills/icp-lead-scoring/SKILL.md`.
2. Run `python3 scripts/score_leads_pipeline.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
