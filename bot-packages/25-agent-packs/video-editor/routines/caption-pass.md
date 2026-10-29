# Routine: Weekday caption pass (`caption-pass`)

- **Agent:** AgentScout Video Editor Agent (`video-editor`)
- **Company:** {{YOUR_COMPANY}} (`{{YOUR_DOMAIN}}`)
- **Schedule (cron):** `0 15 * * 1-5` (`{{YOUR_TIMEZONE}}`)
- **Skill:** `skills/shortform-cut-captions/SKILL.md`
- **Helper Script:** `scripts/format_captions_and_cuts.py`
- **Approval Gate:** Mandatory owner review by {{YOUR_OWNER_NAME}} before any external action.

## Instructions

Format captions and a cut list for the latest transcript from {{YOUR_COMPANY}}. Draft only.

1. Load `context/business-profile.md` and `skills/shortform-cut-captions/SKILL.md`.
2. Run `python3 scripts/format_captions_and_cuts.py --dry-run` (or pass the latest input file for {{YOUR_COMPANY}}).
3. Draft the output and hold for {{YOUR_OWNER_NAME}} approval. Never send, post, spend, delete, or file automatically.
