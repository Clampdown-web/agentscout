---
id: monday-new-member-onboarding
title: "Monday new-member welcome & FAQ check"
cron: "0 9 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/community_health_score.py"
skill: "skills/community-health/SKILL.md"
---

# Routine: Monday new-member welcome & FAQ check (`monday-new-member-onboarding`)

- **Schedule:** `0 9 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Community Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/community_health_score.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/community_health_score.py to list quiet new members and repeated questions that need a new FAQ entry for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/community-health/SKILL.md`.
2. Run `python3 scripts/community_health_score.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
