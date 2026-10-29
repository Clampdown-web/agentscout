---
id: weekly-scope
title: "Weekly scope review"
cron: "0 9 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/model_product_pricing.py"
skill: "skills/pricing-and-mvp-scope/SKILL.md"
---

# Routine: Weekly scope review (`weekly-scope`)

- **Schedule:** `0 9 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Product Builder Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/model_product_pricing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Re-score the backlog for {{YOUR_COMPANY}} and name anything that snuck into the MVP.

1. Read `context/business-profile.md` and `skills/pricing-and-mvp-scope/SKILL.md`.
2. Run `python3 scripts/model_product_pricing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
