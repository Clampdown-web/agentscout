# Routine: Thursday pricing & feature matrix check (`thursday-pricing-battlecard-check`)

- **Agent:** AgentScout Market Researcher Agent (`market-researcher`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 11 * * 4` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/competitor-diff/SKILL.md`
- **Helper Script:** `scripts/competitor_diff_check.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/competitor_diff_check.py on saved competitor snapshots for {{YOUR_COMPANY}} and verify every claim has a dated URL.

1. Load `context/business-profile.md` and `skills/competitor-diff/SKILL.md`.
2. Run `python3 scripts/competitor_diff_check.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
