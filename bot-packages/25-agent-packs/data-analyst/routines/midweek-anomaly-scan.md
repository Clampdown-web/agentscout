---
id: midweek-anomaly-scan
title: "Midweek revenue & churn anomaly scan"
cron: "0 9 * * 3"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/analyze_kpi_csv.py"
skill: "skills/kpi-csv-analyst/SKILL.md"
---

# Routine: Midweek revenue & churn anomaly scan (`midweek-anomaly-scan`)

- **Schedule:** `0 9 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Data Analyst Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/analyze_kpi_csv.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/analyze_kpi_csv.py on the latest export for {{YOUR_COMPANY}} and flag any z-score anomalies.

1. Read `context/business-profile.md` and `skills/kpi-csv-analyst/SKILL.md`.
2. Run `python3 scripts/analyze_kpi_csv.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
