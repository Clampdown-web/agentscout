---
name: ar-aging
description: "Tracks unpaid invoices by aging bucket (3, 7, 14, and 30+ days past due) and drafts polite, relationship-safe payment reminders with direct checkout links so you get paid on time. Use for invoice chaser work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Invoice Chaser Agent: Polite, automated overdue invoice reminders & AR aging reports

This skill trains an assistant to do **invoice chaser** work for **{{YOUR_COMPANY}}** (Tracks unpaid invoices by aging bucket (3, 7, 14, and 30+ days past due) and drafts polite, relationship-safe payment reminders with direct checkout links so you get paid on time.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Polite, automated overdue invoice reminders & AR aging reports".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Every note includes the payment link and the invoice number.
- Tone climbs with age: upcoming, polite, firm, owner. It does not start at a threat.
- A written dispute pauses the ladder.
- Late fees exist only when the contract says so.
- Buckets are current, 1-30, 31-60, 61-90, and older.
- Past 30 days, {{YOUR_OWNER_NAME}} sees the note before it goes out.

## Workflow

### 1. Age the book

Run scripts/aging_ar_report.py as of today.

### 2. Draft the matching note

Use the tone the bucket implies. Keep it short.

### 3. Attach the link

One URL per invoice. Do not make them hunt.

### 4. Pause disputes

If they wrote that the invoice is wrong, stop the sequence and summarize the dispute.

### 5. Escalate

90 days and safety issues go to the owner with the history in one page.


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
python3 scripts/aging_ar_report.py --help
python3 scripts/aging_ar_report.py --self-test
python3 scripts/aging_ar_report.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-dunning` at `0 9 * * 1-5`: Dunning draft queue
- `weekly-aging` at `0 9 * * 1`: Weekly AR aging
- `thursday-dispute-escalation-review` at `0 14 * * 4`: Thursday 30+ day & disputed invoice review

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- AR Aging Tracker
- Polite Follow-Ups
- Approval-First
