# Routine: Morning P0 & refund SLA sweep (`daily-sla-escalation-sweep`)

- **Agent:** AgentScout Customer Support Agent (`customer-support`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 9 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/support-ticket-triage/SKILL.md`
- **Helper Script:** `scripts/triage_support_tickets.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Surface open P0 safety/legal tickets and pending refund requests for {{YOUR_COMPANY}} for owner approval.

1. Load `context/business-profile.md` and `skills/support-ticket-triage/SKILL.md`.
2. Run `python3 scripts/triage_support_tickets.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
