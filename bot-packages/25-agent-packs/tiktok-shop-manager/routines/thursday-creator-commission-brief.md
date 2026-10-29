---
id: thursday-creator-commission-brief
title: "Thursday affiliate script & commission check"
cron: "0 13 * * 4"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/optimize_shop_listing.py"
skill: "skills/shop-listing-optimizer/SKILL.md"
---

# Routine: Thursday affiliate script & commission check (`thursday-creator-commission-brief`)

- **Schedule:** `0 13 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout TikTok Shop Manager Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/optimize_shop_listing.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Run scripts/optimize_shop_listing.py to model creator affiliate commissions and 15-second shoppable video briefs for {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/shop-listing-optimizer/SKILL.md`.
2. Run `python3 scripts/optimize_shop_listing.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
