---
name: ad-roas-rules
description: "Judge campaigns with written ROAS and CPA rules and a creative matrix you can actually test. Use for meta ads agent work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Meta Ads Agent: Runs and scales your ads

This skill trains an assistant to do **meta ads agent** work for **{{YOUR_COMPANY}}** (Judge campaigns with written ROAS and CPA rules and a creative matrix you can actually test.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Runs and scales your ads".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Change one cell of the hook, body, or call to action. A new everything is not a test.
- Do not kill a campaign that has not spent enough to learn.
- Scale only after the efficiency bar and a minimum conversion count.
- Fatigue is frequency up and click-through down, together.
- Every ad URL carries source, medium, campaign, and content tags.
- Special-category ads follow the platform's housing, credit, and employment rules. When unsure, stop.

## Workflow

### 1. Load the export

Spend, revenue, impressions, clicks, conversions, frequency.

### 2. Evaluate

Run scripts/evaluate_ad_roas.py with the targets from the business profile.

### 3. Write the matrix

Three hooks, three bodies, three calls to action. Mark which cell is live.

### 4. Check tracking

Open one ad URL and confirm the tags survive the redirect.

### 5. Ask before spend moves

{{YOUR_OWNER_NAME}} approves every kill or scale.


## Output

Return:

1. The decision or draft in plain sentences.
2. The numbers the script printed, unchanged.
3. A needs-review list.
4. The exact approval you still need from {{YOUR_OWNER_NAME}}.

## Self-check

- The company name in the draft is {{YOUR_COMPANY}}, not a sample brand left in by accident.
- Every external claim has a source the owner supplied.
- You did not send, post, pay, delete, or file.
- The script exit code was 0 on a dry run before you trusted a new file.
- Support path {{YOUR_SUPPORT_EMAIL}} is the only public contact you invent.

## Script

```bash
python3 scripts/evaluate_ad_roas.py --help
python3 scripts/evaluate_ad_roas.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-ads` at `0 8 * * 1-5`: Daily ad rules check
- `weekly-creative` at `0 11 * * 4`: Weekly creative refresh

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
