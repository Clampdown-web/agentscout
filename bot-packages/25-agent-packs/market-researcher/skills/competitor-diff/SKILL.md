---
name: competitor-diff
description: "Compare a competitor on price and features with a source URL and a date on every claim. Use for market researcher work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Market Researcher: Tracks your competitors

This skill trains an assistant to do **market researcher** work for **{{YOUR_COMPANY}}** (Compare a competitor on price and features with a source URL and a date on every claim.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Tracks your competitors".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- No source URL, no claim. A memory of a pricing page is not a source.
- Date the snapshot. A price from last quarter is history, not their offer.
- Diff features as a set. Marketing adjectives are not features.
- If they are cheaper, say who that plan is for.
- Review mining quotes the review. It does not launder it into your voice.
- A launch is a dated change, not a rumor in a chat.

## Workflow

### 1. Snapshot both sides

Name, price, feature list, source URL, as-of date.

### 2. Diff

Run scripts/competitor_diff_check.py.

### 3. Write the matrix

Rows are jobs to be done. Columns are you and them. Cells are facts.

### 4. Mine reviews

Group pains only when you can point at the wording.

### 5. Watch list

The URLs to re-check next week. Nothing else.


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
python3 scripts/competitor_diff_check.py --help
python3 scripts/competitor_diff_check.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-diff` at `0 9 * * 1`: Weekly competitor diff

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
