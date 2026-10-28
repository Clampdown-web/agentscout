---
name: social-hook-desk
description: "Score hooks, format a native post, and keep a calendar the owner can approve. Use for social media manager work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Social Media Manager: Plans and posts every day

This skill trains an assistant to do **social media manager** work for **{{YOUR_COMPANY}}** (Score hooks, format a native post, and keep a calendar the owner can approve.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Plans and posts every day".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- A hook with a number and a concrete noun beats a tease.
- Write for the platform's length. Do not paste the LinkedIn post into a short caption.
- Three to five pillars. If you cannot name them, you are improvising.
- Reply to real comments before you invent tomorrow's post.
- Tag links with a source you can read later.
- Best time is the time your own account already earns attention, not a generic chart.

## Workflow

### 1. Score the hooks

Run scripts/score_social_hooks.py on today's options.

### 2. Format the winner

Thread, caption, or single post inside the character limit.

### 3. Add the link tags

Source, medium, campaign. Campaign is the offer, not the date alone.

### 4. Queue, don't post

{{YOUR_OWNER_NAME}} approves the send.

### 5. Note the result

Tomorrow, record whether the specific hook beat the vague one.


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
python3 scripts/score_social_hooks.py --help
python3 scripts/score_social_hooks.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-hooks` at `0 8 * * 1-5`: Daily hook score
- `weekly-calendar` at `0 11 * * 5`: Next week's calendar

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
