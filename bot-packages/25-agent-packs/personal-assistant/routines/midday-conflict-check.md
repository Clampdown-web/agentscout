# Routine: Midday calendar conflict & prep check (`midday-conflict-check`)

- **Agent:** AgentScout Personal Assistant Agent (`personal-assistant`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 12 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/daily-exec-briefing/SKILL.md`
- **Helper Script:** `scripts/daily_exec_briefing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Check afternoon holds, travel gaps, and next-day meeting prep questions for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}.

1. Load `context/business-profile.md` and `skills/daily-exec-briefing/SKILL.md`.
2. Run `python3 scripts/daily_exec_briefing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
