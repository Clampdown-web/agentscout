---
name: kpi-csv-analyst
description: "Turn a KPI export into rates, a simple LTV, and a short narrative a founder can read. Use for data analyst work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Data Analyst: Weekly reports and insights

This skill trains an assistant to do **data analyst** work for **{{YOUR_COMPANY}}** (Turn a KPI export into rates, a simple LTV, and a short narrative a founder can read.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Weekly reports and insights".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Define the metric before you compute it. Name the numerator and the denominator.
- Check nulls, duplicate months, and a single month that is an order of magnitude off.
- An anomaly is a z-score plus a sentence, not a chart decoration.
- LTV from ARPU divided by logo churn is directional. Say so.
- Three bullets of 'so what' beat a gallery of charts.
- If the export and the finance system disagree, stop and show both numbers.

## Workflow

### 1. Profile the file

Confirm the month column is unique and the units are currency or counts, not a mix.

### 2. Compute

Run scripts/analyze_kpi_csv.py.

### 3. Narrate

What moved, why it might have moved, what you would check next.

### 4. Separate fact from guess

Label every cause you did not measure as a hypothesis.

### 5. Hand it over

{{YOUR_OWNER_NAME}} decides what gets repeated in a customer or investor note.


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
python3 scripts/analyze_kpi_csv.py --help
python3 scripts/analyze_kpi_csv.py --self-test
python3 scripts/analyze_kpi_csv.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-kpi` at `0 8 * * 1`: Weekly KPI narrative
- `midweek-anomaly-scan` at `0 9 * * 3`: Midweek revenue & churn anomaly scan
- `monthly-cohort-ltv-pack` at `0 9 1 * *`: Monthly LTV & retention summary

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
