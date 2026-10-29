---
id: page-check
title: "Landing page UX check"
cron: "0 14 * * 3"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/check_landing_page_ux.py"
skill: "skills/landing-page-ux-check/SKILL.md"
---

# Routine: Landing page UX check (`page-check`)

- **Schedule:** `0 14 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Web Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/check_landing_page_ux.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run the UX check on the current landing HTML for {{YOUR_COMPANY}}. Report issues. Do not deploy.

1. Read `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
