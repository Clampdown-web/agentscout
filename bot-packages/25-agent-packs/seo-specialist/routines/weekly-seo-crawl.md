---
id: weekly-seo-crawl
title: "Weekly SEO and AEO audit"
cron: "0 7 * * 1"
timezone: "{{YOUR_TIMEZONE}}"
requires_approval: true
script: "scripts/seo_site_audit.py"
skill: "skills/seo-aeo-site-audit/SKILL.md"
---

# Routine: Weekly SEO and AEO audit (`weekly-seo-crawl`)

- **Schedule:** `0 7 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Role:** AgentScout SEO Specialist Agent for **{{YOUR_COMPANY}}** (`{{YOUR_DOMAIN}}`)
- **Helper CLI:** `python3 scripts/seo_site_audit.py --self-test`
- **Approval Gate:** Drafts only. Never send, post, spend, delete, or file without explicit approval from **{{YOUR_OWNER_NAME}}**.

## Instructions

Audit the priority URLs for {{YOUR_COMPANY}}. Report issues only. Do not change the live site.

1. Read `context/business-profile.md` and `skills/seo-aeo-site-audit/SKILL.md`.
2. Run `python3 scripts/seo_site_audit.py --dry-run` (or pass `--input` with the latest export for **{{YOUR_COMPANY}}**).
3. Prepare the structured markdown report and action queue for **{{YOUR_OWNER_NAME}}**.
