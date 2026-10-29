---
id: ad-creative-spec-pass
title: "Thursday ad creative spec pass"
cron: "0 10 * * 4"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/generate_brand_card_spec.py"
skill: "skills/brand-card-system/SKILL.md"
---

# Routine: Thursday ad creative spec pass (`ad-creative-spec-pass`)

- **Schedule:** `0 10 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Graphic Designer Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/generate_brand_card_spec.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Generate multi-ratio ad creative specs (1:1, 9:16, 1.91:1) and contrast checks for {{YOUR_COMPANY}}. Draft only.

1. Read `context/business-profile.md` and `skills/brand-card-system/SKILL.md`.
2. Run `python3 scripts/generate_brand_card_spec.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
