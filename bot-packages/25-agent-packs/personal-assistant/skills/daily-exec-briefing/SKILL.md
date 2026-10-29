---
name: daily-exec-briefing
description: "Starts your morning with a clean summary of urgent emails, calendar conflicts, and top 3 action items, plus 1-page dossier briefs before every call. Keeps your day organized without noise. Use for personal assistant work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Personal Assistant Agent: Morning inbox digest, daily priorities & meeting prep briefs

This skill trains an assistant to do **personal assistant** work for **{{YOUR_COMPANY}}** (Starts your morning with a clean summary of urgent emails, calendar conflicts, and top 3 action items, plus 1-page dossier briefs before every call. Keeps your day organized without noise.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Morning inbox digest, daily priorities & meeting prep briefs".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Do, schedule, delegate, defer. Urgent and unimportant is a delegation, not a crisis.
- Never delete mail. Archive only when the owner has said that folder is safe.
- A conflict is two holds that overlap. Propose a move. Do not decline either.
- The brief leads with the one decision that cannot wait.
- Meeting prep is a page of questions, not a biography of the guest.
- Travel items stay on a checklist until a confirmation number exists.

## Workflow

### 1. Collect the day

Inbox items, calendar holds, and open trips for {{YOUR_OWNER_NAME}}.

### 2. Sort

Run scripts/daily_exec_briefing.py.

### 3. Write the brief

Five lines: decision, conflicts, waiting-on, today's meetings, travel gaps.

### 4. Prep the next meeting

Goal, their last ask, and the question that would make the meeting useful.

### 5. Track follow-ups

Anything promised gets an owner and a date.


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
python3 scripts/daily_exec_briefing.py --help
python3 scripts/daily_exec_briefing.py --self-test
python3 scripts/daily_exec_briefing.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `morning-brief` at `0 7 * * 1-5`: Morning briefing
- `friday-review` at `0 16 * * 5`: Friday weekly review
- `midday-conflict-check` at `0 12 * * 1-5`: Midday calendar conflict & prep check

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Morning Executive Brief
- Meeting Dossiers
- Zero Telemetry
