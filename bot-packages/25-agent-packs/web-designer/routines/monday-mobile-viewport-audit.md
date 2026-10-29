---
id: monday-mobile-viewport-audit
title: "Monday 360px/390px mobile overflow audit"
cron: "0 10 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/check_landing_page_ux.py"
skill: "skills/landing-page-ux-check/SKILL.md"
---

# Routine: Monday 360px/390px mobile overflow audit (`monday-mobile-viewport-audit`)

- **Schedule:** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Web Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/check_landing_page_ux.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/check_landing_page_ux.py across key landing pages for {{YOUR_COMPANY}} to verify zero horizontal scroll and alt coverage.

1. Read `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
