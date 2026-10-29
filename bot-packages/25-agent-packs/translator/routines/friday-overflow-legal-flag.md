---
id: friday-overflow-legal-flag
title: "Friday UI length & legal/pricing string review"
cron: "0 14 * * 5"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/verify_i18n_keys.py"
skill: "skills/i18n-key-parity/SKILL.md"
---

# Routine: Friday UI length & legal/pricing string review (`friday-overflow-legal-flag`)

- **Schedule:** `0 14 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout Translator Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/verify_i18n_keys.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Flag translated strings that exceed UI button length budgets or require human review for pricing/legal terms at {{YOUR_COMPANY}}.

1. Read `context/business-profile.md` and `skills/i18n-key-parity/SKILL.md`.
2. Run `python3 scripts/verify_i18n_keys.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
