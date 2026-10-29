---
id: daily-pipeline
title: "Candidate pipeline nudge"
cron: "30 9 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_candidate_rubric.py"
skill: "skills/candidate-rubric/SKILL.md"
---

# Routine: Candidate pipeline nudge (`daily-pipeline`)

- **Schedule:** `30 9 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Recruiter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_candidate_rubric.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

List candidates with no touch in three business days. Draft the next note. Do not send.

1. Read `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
