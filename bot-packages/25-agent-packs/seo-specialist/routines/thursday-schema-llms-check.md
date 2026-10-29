# Routine: Thursday JSON-LD & llms.txt check (`thursday-schema-llms-check`)

- **Agent:** AgentScout SEO Specialist Agent (`seo-specialist`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/seo-aeo-site-audit/SKILL.md`
- **Helper Script:** `scripts/seo_site_audit.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Validate Organization/Product JSON-LD parity and llms.txt citations across saved pages for {{YOUR_COMPANY}}. Report only.

1. Load `context/business-profile.md` and `skills/seo-aeo-site-audit/SKILL.md`.
2. Run `python3 scripts/seo_site_audit.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
