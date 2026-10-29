---
id: tuesday-scorecard-calibration
title: "Tuesday rubric & scorecard audit"
cron: "0 10 * * 2"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_candidate_rubric.py"
skill: "skills/candidate-rubric/SKILL.md"
---

# Routine: Tuesday rubric & scorecard audit (`tuesday-scorecard-calibration`)

- **Schedule:** `0 10 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Recruiter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_candidate_rubric.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/score_candidate_rubric.py on new applicants for {{YOUR_COMPANY}} and flag any protected-trait notes for human review.

1. Read `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
