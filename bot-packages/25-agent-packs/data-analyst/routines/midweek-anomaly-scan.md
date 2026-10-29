# Routine: Midweek revenue & churn anomaly scan (`midweek-anomaly-scan`)

- **Agent:** AgentScout Data Analyst Agent (`data-analyst`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/kpi-csv-analyst/SKILL.md`
- **Helper Script:** `scripts/analyze_kpi_csv.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/analyze_kpi_csv.py on the latest export for {{YOUR_COMPANY}} and flag any z-score anomalies.

1. Load `context/business-profile.md` and `skills/kpi-csv-analyst/SKILL.md`.
2. Run `python3 scripts/analyze_kpi_csv.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
