---
name: newsletter-issue-score
description: "Shape a weekly issue, score the subject and preview, and keep the list clean. Use for email marketer work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Email Marketer: Newsletters that sell

This skill trains an assistant to do **email marketer** work for **{{YOUR_COMPANY}}** (Shape a weekly issue, score the subject and preview, and keep the list clean.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Newsletters that sell".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- One story per issue. A second offer belongs next week.
- The preview text finishes the subject. It does not repeat it.
- Write the plain-text twin with the same links.
- Segment by behavior you measured, not by a persona you like.
- A win-back is one honest note to quiet readers, then a sunset.
- Unsubscribe is a feature. Hide it and you buy complaints.

## Workflow

### 1. Pick the segment

Name who receives this issue and why they are in the file.

### 2. Draft subject pairs

Two subjects, one preview, one body.

### 3. Score it

Run scripts/score_newsletter_issue.py and fix generic subjects and missing unsubscribe links.

### 4. Check the links

Every HTML link exists in the plain-text twin.

### 5. Schedule only after approval

{{YOUR_OWNER_NAME}} picks the winner subject.


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
python3 scripts/score_newsletter_issue.py --help
python3 scripts/score_newsletter_issue.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-issue` at `0 9 * * 2`: Weekly newsletter draft
- `monthly-hygiene` at `0 9 1 * *`: List hygiene note

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
