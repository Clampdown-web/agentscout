# Content Strategist Agent quick start

Built by AgentScout

![AgentScout wordmark](assets/logo-wordmark-dark.svg)

[AgentScout Bot Store](https://agentscouthq.com/bot-store/)

Package for **{{YOUR_COMPANY}}**. Maps buyer questions into a 30-day content calendar across blog, newsletter, YouTube, and social, turning every flagship article or video into 5 channel-ready assets.

## 1. Fill the profile

Edit `context/business-profile.md` or `templates/workspace-config.example.json`. Then run:

```bash
python3 scripts/setup_workspace.py --help
python3 scripts/setup_workspace.py --self-test
```

Add `--apply` with `--company "{{YOUR_COMPANY}}"`, `--domain "{{YOUR_DOMAIN}}"`, `--support-email "{{YOUR_SUPPORT_EMAIL}}"`, `--owner-name "{{YOUR_OWNER_NAME}}"`, and optionally `--mcp-url "{{YOUR_MCP_SERVER_URL}}"` when you are ready to replace placeholders across the package.

## 2. Prove the script

```bash
python3 scripts/generate_30day_calendar.py --help
python3 scripts/generate_30day_calendar.py --self-test
python3 scripts/generate_30day_calendar.py --dry-run
```

All commands exit 0. `--self-test` and `--dry-run` print a JSON report from built-in sample rows with zero network calls and zero telemetry.

## 3. Scheduled Routines Included (3 Cron Routines)

| Routine ID | Cron Schedule (`{{YOUR_TIMEZONE}}`) | Title |
| --- | --- | --- |
| `monthly-calendar` | `0 10 1 * *` | 30-day calendar |
| `quarterly-refresh` | `0 10 1 1,4,7,10 *` | Decay and refresh list |
| `weekly-repurpose-briefs` | `0 10 * * 1` | Weekly pillar brief & 1-to-4 repurpose plan |

## 4. Load the skill

| Platform | What to open |
| --- | --- |
| Grok Bot | `system-prompt.md` (`SYSTEM.md`), `skills/thirty-day-calendar/SKILL.md`, `routines/routines.json` |
| Claude Code | `CLAUDE.md` and `skills/thirty-day-calendar/SKILL.md` |
| Cursor | `.cursorrules` and `AGENTS.md` |
| OpenAI Codex | `AGENTS.md` |
| Windsurf | `AGENTS.md` |
| Cline | `AGENTS.md` and `.cursorrules` |
| GitHub Copilot | `AGENTS.md` |
| Lovable | Upload the ZIP under Workspace settings → Skills → Add → Upload ZIP. `LOVABLE.md` is the workspace note. |

## 5. Approval Gate

Nothing in this package sends email, posts, spends, deletes, or files. {{YOUR_OWNER_NAME}} does that after reading the draft.
