---
id: friday-cta-contrast-review
title: "Friday above-the-fold CTA & contrast check"
cron: "0 15 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/check_landing_page_ux.py"
skill: "skills/landing-page-ux-check/SKILL.md"
---

# Routine: Friday above-the-fold CTA & contrast check (`friday-cta-contrast-review`)

- **Schedule:** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Web Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/check_landing_page_ux.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Verify hero CTA clarity and 4.5:1 text contrast pairs on updated templates for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
