# Routine: Decay and refresh list (`quarterly-refresh`)

- **Agent:** AgentScout Content Strategist Agent (`content-strategist`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 1 1,4,7,10 *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/thirty-day-calendar/SKILL.md`
- **Helper Script:** `scripts/generate_30day_calendar.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

List URLs that should be updated before new topics are added.

1. Load `context/business-profile.md` and `skills/thirty-day-calendar/SKILL.md`.
2. Run `python3 scripts/generate_30day_calendar.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
