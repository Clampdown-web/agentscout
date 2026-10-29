---
id: weekly-asset-batch
title: "Weekly social asset batch"
cron: "0 10 * * 2"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_brand_card_spec.py"
skill: "skills/brand-card-system/SKILL.md"
---

# Routine: Weekly social asset batch (`weekly-asset-batch`)

- **Schedule:** `0 10 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Graphic Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_brand_card_spec.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Produce this week's card specs for {{YOUR_COMPANY}} from the approved brand tokens. Draft only. Do not publish.

1. Read `context/business-profile.md` and `skills/brand-card-system/SKILL.md`.
2. Run `python3 scripts/generate_brand_card_spec.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
