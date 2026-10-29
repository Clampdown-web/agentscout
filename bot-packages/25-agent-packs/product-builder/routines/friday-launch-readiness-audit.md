---
id: friday-launch-readiness-audit
title: "Friday MVP & launch readiness checklist"
cron: "0 15 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/model_product_pricing.py"
skill: "skills/pricing-and-mvp-scope/SKILL.md"
---

# Routine: Friday MVP & launch readiness checklist (`friday-launch-readiness-audit`)

- **Schedule:** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Product Builder Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/model_product_pricing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Verify PRD non-goals, baseline success metrics, and live support paths before any release at {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/pricing-and-mvp-scope/SKILL.md`.
2. Run `python3 scripts/model_product_pricing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
