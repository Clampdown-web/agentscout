# Routine: Inbox triage (`hourly-triage`)

- **Agent:** AgentScout Customer Support Agent (`customer-support`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `15 * * * *` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/support-ticket-triage/SKILL.md`
- **Helper Script:** `scripts/triage_support_tickets.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Triage new tickets for {{YOUR_COMPANY}}. Draft replies. Send nothing.

1. Load `context/business-profile.md` and `skills/support-ticket-triage/SKILL.md`.
2. Run `python3 scripts/triage_support_tickets.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
