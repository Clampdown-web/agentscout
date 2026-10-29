---
id: monthly-brand-consistency-audit
title: "Monthly brand token & contrast audit"
cron: "0 11 1 * *"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_brand_card_spec.py"
skill: "skills/brand-card-system/SKILL.md"
---

# Routine: Monthly brand token & contrast audit (`monthly-brand-consistency-audit`)

- **Schedule:** `0 11 1 * *` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Graphic Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_brand_card_spec.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Audit recent visual assets and thumbnails against {{YOUR_COMPANY}} hex tokens and 4.5:1 contrast rules. Report only.

1. Read `context/business-profile.md` and `skills/brand-card-system/SKILL.md`.
2. Run `python3 scripts/generate_brand_card_spec.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
