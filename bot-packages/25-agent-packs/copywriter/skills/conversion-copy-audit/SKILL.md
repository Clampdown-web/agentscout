---
name: conversion-copy-audit
description: "Draft and edit offers with a clear problem, proof, and a single next step. Use for copywriter work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Copywriter: Captions, emails, sales pages

This skill trains an assistant to do **copywriter** work for **{{YOUR_COMPANY}}** (Draft and edit offers with a clear problem, proof, and a single next step.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Captions, emails, sales pages".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Name the reader's situation before you name the product.
- PAS for a pain the buyer already feels. AIDA when they are still browsing.
- One claim, one proof, one button above the fold.
- Replace a vague intensifier with a number, a noun, or a customer sentence.
- Read the line aloud. If you run out of breath, split the sentence.
- A headline test needs a hypothesis, not three random puns.

## Workflow

### 1. Collect the voice

Pull phrases customers already use from reviews or call notes for {{YOUR_COMPANY}}.

### 2. Draft three headlines

Each headline gets a hypothesis: who it selects and what it promises.

### 3. Audit the draft

Run scripts/audit_sales_copy.py. Fix weasel words and any missing proof before you polish tone.

### 4. Handle objections

Write the objection in the customer's words, then the answer under it.

### 5. Stop at a draft

Do not publish the page. Hand it to {{YOUR_OWNER_NAME}} with the readability number.


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
python3 scripts/audit_sales_copy.py --help
python3 scripts/audit_sales_copy.py --self-test
python3 scripts/audit_sales_copy.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `copy-pass` at `0 9 * * 3`: Midweek copy pass
- `weekly-headline-variants` at `0 9 * * 1`: Monday headline & hook variants
- `friday-objection-refresh` at `0 14 * * 5`: Friday customer objection refresh

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
