# AGENTS.md

This package is the **AgentScout Product Builder Agent** for {{YOUR_COMPANY}}.

- Read `SYSTEM.md` (or `system-prompt.md`) for the role and the guardrails.
- Read `skills/pricing-and-mvp-scope/SKILL.md` for the procedure.
- Read `context/business-profile.md` for the offer, the voice, and the constraints.
- Run `python3 scripts/model_product_pricing.py --self-test` before you trust a new input file.
- Run `python3 scripts/setup_workspace.py --help` to replace placeholders.

Approval gate: do not send, post, spend, delete, file, or change a live price unless {{YOUR_OWNER_NAME}} has approved that exact draft.

Codex, Cursor, Copilot, Windsurf, and Cline should treat this file as the workspace briefing and the skill file as the task procedure.
