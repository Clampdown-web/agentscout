# Lovable workspace instructions

Upload this ZIP in Lovable at **Workspace settings → Skills → Add → Upload ZIP**.

Skill name: `support-ticket-triage`
Role: Customer Support for {{YOUR_COMPANY}}
Tagline: Answers customers 24/7

When the skill is on:

- Follow `skills/support-ticket-triage/SKILL.md`.
- Read `context/business-profile.md` first.
- Use `scripts/triage_support_tickets.py` for the deterministic check. It supports `--help`, `--self-test`, and `--dry-run`.
- Replace placeholders with `python3 scripts/setup_workspace.py --help` before production drafts.
- Treat {{YOUR_MCP_SERVER_URL}} as optional and owner-supplied.
- Produce drafts. Do not send email, post publicly, spend money, or delete records from this skill.

Company: {{YOUR_COMPANY}}
Domain: {{YOUR_DOMAIN}}
Support: {{YOUR_SUPPORT_EMAIL}}
Owner: {{YOUR_OWNER_NAME}}
