# Meta Ads Agent quick start

Built by AgentScout

![AgentScout wordmark](https://agentscouthq.com/logo-wordmark-dark.png)

[AgentScout Bot Store](https://agentscouthq.com/bot-store/)

Package for **{{YOUR_COMPANY}}**. Judge campaigns with written ROAS and CPA rules and a creative matrix you can actually test.

## 1. Fill the profile

Edit `context/business-profile.md`. Then run:

```bash
python3 setup_workspace.py --help
python3 setup_workspace.py --dry-run
```

Add `--apply` with `--company`, `--domain`, `--support-email`, `--owner-name`, and optionally `--mcp-url` when you are ready to replace placeholders.

## 2. Prove the script

```bash
python3 scripts/evaluate_ad_roas.py --help
python3 scripts/evaluate_ad_roas.py --dry-run
```

Both commands exit 0. `--dry-run` prints a JSON report from built-in sample rows.

## 3. Load the skill

| Platform | What to open |
| --- | --- |
| Grok Bot | `SYSTEM.md`, `skills/ad-roas-rules/SKILL.md`, `routines/routines.json` |
| Claude Code | `CLAUDE.md` and the skill file |
| Cursor | `.cursorrules` and `AGENTS.md` |
| OpenAI Codex | `AGENTS.md` |
| Windsurf | `AGENTS.md` |
| Cline | `AGENTS.md` and `.cursorrules` |
| GitHub Copilot | `AGENTS.md` |
| Lovable | Upload the ZIP under Workspace settings → Skills → Add → Upload ZIP. `LOVABLE.md` is the workspace note. |

## 4. Approval

Nothing in this package sends email, posts, spends, deletes, or files. {{YOUR_OWNER_NAME}} does that after reading the draft.
