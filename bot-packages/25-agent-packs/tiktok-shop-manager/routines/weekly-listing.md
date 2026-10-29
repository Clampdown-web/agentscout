---
id: weekly-listing
title: "Weekly listing audit"
cron: "0 11 * * 2"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/optimize_shop_listing.py"
skill: "skills/shop-listing-optimizer/SKILL.md"
---

# Routine: Weekly listing audit (`weekly-listing`)

- **Schedule:** `0 11 * * 2` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout TikTok Shop Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/optimize_shop_listing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Re-lint the priority products and draft title edits.

1. Read `context/business-profile.md` and `skills/shop-listing-optimizer/SKILL.md`.
2. Run `python3 scripts/optimize_shop_listing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
