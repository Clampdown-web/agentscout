# Appointment Setter Agent quick start

Built by AgentScout

![AgentScout wordmark](assets/logo-wordmark-dark.svg)

[AgentScout Bot Store](https://agentscouthq.com/bot-store/)

Package for **{{YOUR_COMPANY}}**. Follows up with warm inquiries, checks qualification criteria, and sends timezone-aware booking options plus pre-call reminders to cut no-shows. Includes a slot-conflict and reminder generator script.

## 1. Fill the profile

Edit `context/business-profile.md` or `templates/workspace-config.example.json`. Then run:

```bash
python3 scripts/setup_workspace.py --help
python3 scripts/setup_workspace.py --self-test
```

Add `--apply` with `--company "{{YOUR_COMPANY}}"`, `--domain "{{YOUR_DOMAIN}}"`, `--support-email "{{YOUR_SUPPORT_EMAIL}}"`, `--owner-name "{{YOUR_OWNER_NAME}}"`, and optionally `--mcp-url "{{YOUR_MCP_SERVER_URL}}"` when you are ready to replace placeholders across the package.

## 2. Prove the script

```bash
python3 scripts/build_call_briefing.py --help
python3 scripts/build_call_briefing.py --self-test
python3 scripts/build_call_briefing.py --dry-run
```

All commands exit 0. `--self-test` and `--dry-run` print a JSON report from built-in sample rows with zero network calls and zero telemetry.

## 3. Scheduled Routines Included (3 Cron Routines)

| Routine ID | Cron Schedule (`{{YOUR_TIMEZONE}}`) | Title |
| --- | --- | --- |
| `reminder-sweep` | `0 8 * * *` | Reminder and no-show sweep |
| `weekday-inbound-slots` | `0 9,14 * * 1-5` | Inbound lead qualification & slot prep |
| `friday-booking-conversion-review` | `0 16 * * 5` | Weekly show-rate & briefing review |

## 4. Load the skill

| Platform | What to open |
| --- | --- |
| Grok Bot | `system-prompt.md` (`SYSTEM.md`), `skills/call-briefing-slots/SKILL.md`, `routines/routines.json` |
| Claude Code | `CLAUDE.md` and `skills/call-briefing-slots/SKILL.md` |
| Cursor | `.cursorrules` and `AGENTS.md` |
| OpenAI Codex | `AGENTS.md` |
| Windsurf | `AGENTS.md` |
| Cline | `AGENTS.md` and `.cursorrules` |
| GitHub Copilot | `AGENTS.md` |
| Lovable | Upload the ZIP under Workspace settings → Skills → Add → Upload ZIP. `LOVABLE.md` is the workspace note. |

## 5. Approval Gate

Nothing in this package sends email, posts, spends, deletes, or files. {{YOUR_OWNER_NAME}} does that after reading the draft.
