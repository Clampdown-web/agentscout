# Routine: Weekly pillar brief & 1-to-4 repurpose plan (`weekly-repurpose-briefs`)

- **Agent:** AgentScout Content Strategist Agent (`content-strategist`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 1` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/thirty-day-calendar/SKILL.md`
- **Helper Script:** `scripts/generate_30day_calendar.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Turn this week's priority pillar topic for {{YOUR_COMPANY}} into an outline, email angle, short video beat, and FAQ block.

1. Load `context/business-profile.md` and `skills/thirty-day-calendar/SKILL.md`.
2. Run `python3 scripts/generate_30day_calendar.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
