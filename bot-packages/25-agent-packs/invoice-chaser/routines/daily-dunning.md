---
id: daily-dunning
title: "Dunning draft queue"
cron: "0 9 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/aging_ar_report.py"
skill: "skills/ar-aging/SKILL.md"
---

# Routine: Dunning draft queue (`daily-dunning`)

- **Schedule:** `0 9 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Invoice Chaser Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/aging_ar_report.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Draft today's receivable notes for {{YOUR_COMPANY}}. Do not send.

1. Read `context/business-profile.md` and `skills/ar-aging/SKILL.md`.
2. Run `python3 scripts/aging_ar_report.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
