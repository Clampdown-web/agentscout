---
id: wednesday-pricing-tier-check
title: "Wednesday Good/Better/Best pricing model"
cron: "0 11 * * 3"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/model_product_pricing.py"
skill: "skills/pricing-and-mvp-scope/SKILL.md"
---

# Routine: Wednesday Good/Better/Best pricing model (`wednesday-pricing-tier-check`)

- **Schedule:** `0 11 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Product Builder Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/model_product_pricing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/model_product_pricing.py to stress-test unit costs, target margins, and tier boundaries for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/pricing-and-mvp-scope/SKILL.md`.
2. Run `python3 scripts/model_product_pricing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
