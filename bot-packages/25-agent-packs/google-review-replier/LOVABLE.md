# Lovable workspace instructions

Upload this ZIP in Lovable at **Workspace settings → Skills → Add → Upload ZIP**.

Skill name: `review-reply-desk`
Role: Google Review Replier Agent for {{YOUR_COMPANY}}
Tagline: Fast, on-brand replies to every 5-star and critical local review

When the skill is on:

- Follow `skills/review-reply-desk/SKILL.md`.
- Read `context/business-profile.md` first.
- Use `scripts/generate_review_replies.py` for the deterministic check. It supports `--help` and `--dry-run`.
- Replace placeholders with `python3 setup_workspace.py --help` before production drafts.
- Treat {{YOUR_MCP_SERVER_URL}} as optional and owner-supplied.
- Produce drafts. Do not send email, post publicly, spend money, or delete records from this skill.

Company: {{YOUR_COMPANY}}
Domain: {{YOUR_DOMAIN}}
Support: {{YOUR_SUPPORT_EMAIL}}
Owner: {{YOUR_OWNER_NAME}}
