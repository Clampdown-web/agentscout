# Routine: Thursday 30+ day & disputed invoice review (`thursday-dispute-escalation-review`)

- **Agent:** AgentScout Invoice Chaser Agent (`invoice-chaser`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 14 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/ar-aging/SKILL.md`
- **Helper Script:** `scripts/aging_ar_report.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Compile 30+ day overdue accounts and paused disputed invoices for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}. Do not send.

1. Load `context/business-profile.md` and `skills/ar-aging/SKILL.md`.
2. Run `python3 scripts/aging_ar_report.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
