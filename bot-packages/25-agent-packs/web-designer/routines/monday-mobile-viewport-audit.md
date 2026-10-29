# Routine: Monday 360px/390px mobile overflow audit (`monday-mobile-viewport-audit`)

- **Agent:** AgentScout Web Designer Agent (`web-designer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/landing-page-ux-check/SKILL.md`
- **Helper Script:** `scripts/check_landing_page_ux.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/check_landing_page_ux.py across key landing pages for {{YOUR_COMPANY}} to verify zero horizontal scroll and alt coverage.

1. Load `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
