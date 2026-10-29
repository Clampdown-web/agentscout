# Routine: Friday above-the-fold CTA & contrast check (`friday-cta-contrast-review`)

- **Agent:** AgentScout Web Designer Agent (`web-designer`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 15 * * 5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/landing-page-ux-check/SKILL.md`
- **Helper Script:** `scripts/check_landing_page_ux.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Verify hero CTA clarity and 4.5:1 text contrast pairs on updated templates for {{YOUR_COMPANY}}.

1. Load `context/business-profile.md` and `skills/landing-page-ux-check/SKILL.md`.
2. Run `python3 scripts/check_landing_page_ux.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
