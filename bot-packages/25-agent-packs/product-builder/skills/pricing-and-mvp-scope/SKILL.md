---
name: pricing-and-mvp-scope
description: "Turns rough feature ideas and customer requests into scoped PRDs with acceptance criteria, RICE priority scores, QA checklists, and clean changelog notes for your engineering workflow. Use for product builder work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Product Builder Agent: PRDs, user stories, release checklists & feedback prioritization

This skill trains an assistant to do **product builder** work for **{{YOUR_COMPANY}}** (Turns rough feature ideas and customer requests into scoped PRDs with acceptance criteria, RICE priority scores, QA checklists, and clean changelog notes for your engineering workflow.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "PRDs, user stories, release checklists & feedback prioritization".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Write the non-goals in the same sitting as the goals. Scope creep eats the sentence you skipped.
- A feature earns its place with reach, impact, confidence, and effort.
- Price from cost and a target margin, then sense-check it against the buyer's alternative.
- Good, better, and best must be different products, not the same product with a louder adjective.
- The success metric has a baseline and a date.
- Support email is live before the first charge.

## Workflow

### 1. Write the PRD skeleton

Problem, user, success metric, non-goals.

### 2. Score the backlog

Run scripts/model_product_pricing.py.

### 3. Cut the MVP

Keep the flagged core. Move the rest to a later list without apology.

### 4. Model the tiers

Show monthly and the annual equivalent. Name what each tier includes.

### 5. Launch list

Page, payment, receipt, support path, and the first ten users you will talk to.


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
python3 scripts/model_product_pricing.py --help
python3 scripts/model_product_pricing.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-scope` at `0 9 * * 1`: Weekly scope review

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- PRD & RICE Scorer
- Release QA Checklist
- Zero Telemetry
