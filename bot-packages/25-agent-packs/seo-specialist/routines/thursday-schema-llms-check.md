---
id: thursday-schema-llms-check
title: "Thursday JSON-LD & llms.txt check"
cron: "0 10 * * 4"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/seo_site_audit.py"
skill: "skills/seo-aeo-site-audit/SKILL.md"
---

# Routine: Thursday JSON-LD & llms.txt check (`thursday-schema-llms-check`)

- **Schedule:** `0 10 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout SEO Specialist Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/seo_site_audit.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Validate Organization/Product JSON-LD parity and llms.txt citations across saved pages for {{YOUR_COMPANY}}. Report only.

1. Read `context/business-profile.md` and `skills/seo-aeo-site-audit/SKILL.md`.
2. Run `python3 scripts/seo_site_audit.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
