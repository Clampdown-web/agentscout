---
name: community-health
description: "Measure who is quiet, welcome new members, and draft prompts a person can post. Use for community manager work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Community Manager: Keeps your community active

This skill trains an assistant to do **community manager** work for **{{YOUR_COMPANY}}** (Measure who is quiet, welcome new members, and draft prompts a person can post.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Keeps your community active".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- A prompt is a question a member can answer from their own week.
- New members get a welcome, a day-two nudge, and a day-seven check.
- Lurkers are a metric, not a moral failing. Invite once. Do not nag.
- Moderate the behavior against the written code. Do not improvise a new rule in public.
- Personal data and harassment move to {{YOUR_SUPPORT_EMAIL}}.
- FAQ entries come from questions asked twice.

## Workflow

### 1. Score the export

Run scripts/community_health_score.py.

### 2. Draft today's prompt

One question tied to the offer, easy to answer in three lines.

### 3. Onboard the quiet new members

A short welcome that points at the code of conduct.

### 4. Update the FAQ

If the score shows the same confusion, add the answer.

### 5. Re-engage

One note to people dark for a month. Then leave them alone.


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
python3 scripts/community_health_score.py --help
python3 scripts/community_health_score.py --self-test
python3 scripts/community_health_score.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-community` at `0 10 * * 1-5`: Daily community draft
- `weekly-digest` at `0 15 * * 5`: Weekly engagement digest
- `monday-new-member-onboarding` at `0 9 * * 1`: Monday new-member welcome & FAQ check

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
