---
id: midweek-signal-sweep
title: "Midweek buying-signal sweep"
cron: "0 13 * * 3"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_leads_pipeline.py"
skill: "skills/icp-lead-scoring/SKILL.md"
---

# Routine: Midweek buying-signal sweep (`midweek-signal-sweep`)

- **Schedule:** `0 13 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Lead Gen Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_leads_pipeline.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Re-score nurture-band prospects (40-59 pts) for new buying signals at {{YOUR_COMPANY}}. Do not email anyone.

1. Read `context/business-profile.md` and `skills/icp-lead-scoring/SKILL.md`.
2. Run `python3 scripts/score_leads_pipeline.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
