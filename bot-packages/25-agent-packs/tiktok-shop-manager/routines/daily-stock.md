---
id: daily-stock
title: "Inventory alert check"
cron: "0 8 * * 1-5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/optimize_shop_listing.py"
skill: "skills/shop-listing-optimizer/SKILL.md"
---

# Routine: Inventory alert check (`daily-stock`)

- **Schedule:** `0 8 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout TikTok Shop Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/optimize_shop_listing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Check listing stock against the reorder point for {{YOUR_COMPANY}}. Do not change the live listing.

1. Read `context/business-profile.md` and `skills/shop-listing-optimizer/SKILL.md`.
2. Run `python3 scripts/optimize_shop_listing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
