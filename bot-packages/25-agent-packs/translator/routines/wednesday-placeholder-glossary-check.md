# Routine: Midweek placeholder & glossary audit (`wednesday-placeholder-glossary-check`)

- **Agent:** AgentScout Translator Agent (`translator`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 10 * * 3` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/i18n-key-parity/SKILL.md`
- **Helper Script:** `scripts/verify_i18n_keys.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Run scripts/verify_i18n_keys.py across active locale JSON bundles for {{YOUR_COMPANY}} to catch missing keys or broken {{tokens}}.

1. Load `context/business-profile.md` and `skills/i18n-key-parity/SKILL.md`.
2. Run `python3 scripts/verify_i18n_keys.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
