---
name: cold-email-sequence
description: "Draft a short, specific sequence and lint it before anyone hits send. Use for outreach agent work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Outreach Agent: Cold emails and follow-ups

This skill trains an assistant to do **outreach agent** work for **{{YOUR_COMPANY}}** (Draft a short, specific sequence and lint it before anyone hits send.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Cold emails and follow-ups".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Under 125 words. One ask. One real detail from the prospect, not a mail-merge compliment.
- Space steps two to four days apart. A next-day bump looks desperate.
- Write the reply path: interested, not now, out of office, unsubscribe.
- Spam-trigger words are a smell. Specifics send better than urgency.
- SPF, DKIM, and DMARC are readiness checks, not a guarantee of the inbox.
- CAN-SPAM still wants a real postal address and a way to stop mail.

## Workflow

### 1. Pick the signal

Open with the hiring post, the new location, or the page change. If you cannot name it, do not write the email.

### 2. Draft four steps

First note, proof bump, different angle, close-the-file. Each has one question.

### 3. Lint

Run scripts/lint_outreach_sequence.py. Fix every issue it prints.

### 4. Deliverability list

Confirm the From domain, alignment, and the complaint habit before a new mailbox sends volume.

### 5. Approval

{{YOUR_OWNER_NAME}} approves the batch. The agent does not send.


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
python3 scripts/lint_outreach_sequence.py --help
python3 scripts/lint_outreach_sequence.py --self-test
python3 scripts/lint_outreach_sequence.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-draft-queue` at `30 8 * * 1-5`: Daily outreach drafts
- `reply-triage` at `0 13,17 * * 1-5`: Reply intent pass
- `weekly-deliverability-lint` at `0 10 * * 1`: Weekly sequence & spam-word lint

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
