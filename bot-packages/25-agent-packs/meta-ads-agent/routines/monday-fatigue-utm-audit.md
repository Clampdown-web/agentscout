---
id: monday-fatigue-utm-audit
title: "Monday creative fatigue & UTM audit"
cron: "0 9 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/evaluate_ad_roas.py"
skill: "skills/ad-roas-rules/SKILL.md"
---

# Routine: Monday creative fatigue & UTM audit (`monday-fatigue-utm-audit`)

- **Schedule:** `0 9 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Meta Ads Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/evaluate_ad_roas.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Flag high-frequency/falling-CTR ad sets and verify UTM tags across active campaigns for {{YOUR_COMPANY}}. Recommend only.

1. Read `context/business-profile.md` and `skills/ad-roas-rules/SKILL.md`.
2. Run `python3 scripts/evaluate_ad_roas.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
