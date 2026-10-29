# START HERE: AgentScout Graphic Designer Agent

AgentScout Graphic Designer Agent for {{YOUR_COMPANY}} (High-converting ad creatives, social graphics & YouTube thumbnails). Domain placeholder: {{YOUR_DOMAIN}}.

## What's inside

- `SYSTEM.md`, the role instructions for the Graphic Designer Agent
- `skills/brand-card-system/SKILL.md`, the playbook
- `scripts/generate_brand_card_spec.py`, a local Python 3 script (standard library only)
- `routines/`, 3 scheduled routines, starting with Weekly social asset batch
- `setup_workspace.py`, which writes your company name and domain
- `mcp.json`, an optional MCP server entry
- `context/business-profile.md`, the offer, voice, and constraints

## 10-minute setup

1. Import the template. In Grok Bot, create a teammate and paste SYSTEM.md into its instructions. In Lovable, import this ZIP under Workspace settings, then Skills, then Add, then Upload ZIP. Lovable reads skills/brand-card-system/SKILL.md. This folder also includes Claude Code (CLAUDE.md), Cursor (.cursorrules), Codex (AGENTS.md).
2. Replace {{YOUR_COMPANY}} and {{YOUR_DOMAIN}}. From the unzipped folder run `python3 setup_workspace.py --apply --company "Your Company" --domain "yourdomain.com"`. That writes those two values through the package.
3. Connect tools. Open mcp.json and, if your company already runs an MCP server, put that server's URL in the entry. If you do not have one, leave the file unchanged. The file does not connect a tool by itself.
4. Run the first task. From this folder run `python3 scripts/generate_brand_card_spec.py --dry-run`.

## What to expect on the first run

The dry run prints a JSON report from sample rows and exits. It does not email, post, spend, delete, or file anything. The routine "Weekly social asset batch" is a draft for you to read. You decide what leaves the machine.

## Help

Questions about this download: support@agentscouthq.com
