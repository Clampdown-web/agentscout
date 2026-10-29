---
id: friday-hiring-sla-digest
title: "Friday hiring stage SLA digest"
cron: "0 15 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/score_candidate_rubric.py"
skill: "skills/candidate-rubric/SKILL.md"
---

# Routine: Friday hiring stage SLA digest (`friday-hiring-sla-digest`)

- **Schedule:** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Recruiter Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/score_candidate_rubric.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Summarize candidate counts by stage, days-in-stage SLA breaches, and interview prep kits for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/candidate-rubric/SKILL.md`.
2. Run `python3 scripts/score_candidate_rubric.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
