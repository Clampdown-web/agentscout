---
name: icp-lead-scoring
description: "Score prospects you already have, drop duplicates, and hand sales a CSV of people worth a human review. Use for lead gen agent work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Lead Gen Agent: Finds qualified leads daily

This skill trains an assistant to do **lead gen agent** work for **{{YOUR_COMPANY}}** (Score prospects you already have, drop duplicates, and hand sales a CSV of people worth a human review.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Finds qualified leads daily".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Write the ICP and the anti-ICP before you score a single row.
- A buying signal beats a big employee count.
- Dedupe on the domain, not the display name.
- An email that fails a basic shape check does not enter the send queue.
- Log where the row came from. A lead without a source is a rumor.
- Cap the daily batch. A smaller list that sales will touch beats a dump.

## Workflow

### 1. Lock the rubric

Confirm employee band, buyer titles, industries, and disqualifiers for {{YOUR_COMPANY}}.

### 2. Score the file

Run scripts/score_leads_pipeline.py. Read the reason codes, not only the total.

### 3. Drop duplicates

Keep the richest row when two lines share a domain.

### 4. Separate nurture from discard

40-59 points can get a softer offer. Under 40 leaves the queue.

### 5. Optional enrichment

If columns are empty, a person may use a paid vendor such as Apollo, Explorium, or LeadMagic. This package does not call them.

### 6. Export

Write the qualified CSV and stop. {{YOUR_OWNER_NAME}} decides who gets an email.


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
python3 scripts/score_leads_pipeline.py --help
python3 scripts/score_leads_pipeline.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-lead-batch` at `0 8 * * 1-5`: Daily qualified lead batch
- `weekly-icp-refresh` at `0 11 * * 5`: Weekly ICP refresh

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
