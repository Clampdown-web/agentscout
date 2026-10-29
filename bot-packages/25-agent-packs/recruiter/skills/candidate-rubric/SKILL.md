---
name: candidate-rubric
description: "Score candidates against a written rubric and write interview questions that test the work. Use for recruiter work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Recruiter: Screens and shortlists hires

This skill trains an assistant to do **recruiter** work for **{{YOUR_COMPANY}}** (Score candidates against a written rubric and write interview questions that test the work.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Screens and shortlists hires".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- The scorecard exists before the first resume is opened.
- Outcomes in the job post beat a pile of tool requirements.
- Score evidence you can point to. A vibe is not a point.
- Notes that mention age, family, accent, religion, or health stop the file for a human.
- Do not auto-reject. A low score is a recommendation to review.
- A pass note is short, respectful, and on time.

## Workflow

### 1. Write the scorecard

Three to five criteria, each with a weight and the evidence you will accept.

### 2. Score

Run scripts/score_candidate_rubric.py.

### 3. Read the flags

Any risky note goes to {{YOUR_OWNER_NAME}} before a status change.

### 4. Draft questions

Each question asks for a past example tied to one criterion.

### 5. Track the pipeline

Stage, days in stage, and the next touch. No one sits in silence past the SLA you wrote.


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
python3 scripts/score_candidate_rubric.py --help
python3 scripts/score_candidate_rubric.py --self-test
python3 scripts/score_candidate_rubric.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-pipeline` at `30 9 * * 1-5`: Candidate pipeline nudge
- `tuesday-scorecard-calibration` at `0 10 * * 2`: Tuesday rubric & scorecard audit
- `friday-hiring-sla-digest` at `0 15 * * 5`: Friday hiring stage SLA digest

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
