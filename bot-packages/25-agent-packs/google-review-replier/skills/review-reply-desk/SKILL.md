---
name: review-reply-desk
description: "Draft a specific public reply for every review and a private path for anything serious. Use for google review replier work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Google Review Replier: Replies to every review

This skill trains an assistant to do **google review replier** work for **{{YOUR_COMPANY}}** (Draft a specific public reply for every review and a private path for anything serious.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Replies to every review".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Reply inside two days. A late thank-you still beats silence, but the habit is daily.
- Use the name and one detail they actually wrote.
- A keyword may appear once if it fits. Stuffing the city into every sentence reads as spam.
- Never offer a perk to change, delete, or post a review.
- Safety, health, and legal comments leave the public thread immediately.
- Ask happy customers for a review without gating it on a positive score.

## Workflow

### 1. Sort by severity

Run scripts/generate_review_replies.py. P0 drafts escalate before the thank-you notes.

### 2. Edit the thank-you

Add the detail the script could not know. Cut any incentive language.

### 3. Edit the recovery

Apologize for the experience you can see. Move the fix to {{YOUR_SUPPORT_EMAIL}}.

### 4. Track velocity

Note how many reviews arrived and how many still lack a draft.

### 5. Monthly themes

Group repeated complaints so operations can fix the cause, not only the wording.


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
python3 scripts/generate_review_replies.py --help
python3 scripts/generate_review_replies.py --self-test
python3 scripts/generate_review_replies.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-review-drafts` at `0 9 * * *`: Daily review replies
- `monthly-themes` at `0 10 1 * *`: Monthly review themes
- `friday-escalation-check` at `0 15 * * 5`: Weekly P0 complaint & SLA check

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
