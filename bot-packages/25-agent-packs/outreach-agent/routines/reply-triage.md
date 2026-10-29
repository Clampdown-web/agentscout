# Routine: Reply intent pass (`reply-triage`)

- **Agent:** AgentScout Outreach Agent (`outreach-agent`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 13,17 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/cold-email-sequence/SKILL.md`
- **Helper Script:** `scripts/lint_outreach_sequence.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Classify replies as interested, not now, out of office, or unsubscribe. Draft responses. Do not send.

1. Load `context/business-profile.md` and `skills/cold-email-sequence/SKILL.md`.
2. Run `python3 scripts/lint_outreach_sequence.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
