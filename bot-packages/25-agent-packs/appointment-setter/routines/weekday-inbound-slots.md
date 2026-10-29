# Routine: Inbound lead qualification & slot prep (`weekday-inbound-slots`)

- **Agent:** AgentScout Appointment Setter Agent (`appointment-setter`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9,14 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/call-briefing-slots/SKILL.md`
- **Helper Script:** `scripts/build_call_briefing.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Qualify new inbound inquiries for {{YOUR_COMPANY}} and build timezone-matched slot options with scripts/build_call_briefing.py.

1. Load `context/business-profile.md` and `skills/call-briefing-slots/SKILL.md`.
2. Run `python3 scripts/build_call_briefing.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
