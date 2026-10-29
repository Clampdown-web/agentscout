# Routine: Landing page UX check (`page-check`)

- **Agent:** AgentScout Web Designer Agent (`web-designer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 14 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/landing-page-ux-check/SKILL.md`
- **Helper Script:** `scripts/check_landing_page_ux.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run the UX check on the current landing HTML for {{YOUR_COMPANY}}. Report issues. Do not deploy.

1. Load `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
