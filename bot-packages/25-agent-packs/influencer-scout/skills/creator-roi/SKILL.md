---
name: creator-roi
description: "Finds niche creators across YouTube, X, TikTok, and newsletters, scores real audience engagement versus follower inflation, and prepares personalized partnership offers and UTM tracking links. Use for influencer scout work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Influencer Scout Agent: Creator discovery, engagement-rate vetting & sponsorship ROI tracking

This skill trains an assistant to do **influencer scout** work for **{{YOUR_COMPANY}}** (Finds niche creators across YouTube, X, TikTok, and newsletters, scores real audience engagement versus follower inflation, and prepares personalized partnership offers and UTM tracking links.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Creator discovery, engagement-rate vetting & sponsorship ROI tracking".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Audience match matters more than follower count.
- An engagement rate far above the usual range is a review flag, not a verdict.
- CPM is price divided by thousands of followers. It is a planning number, not a promise of reach.
- ROI uses the orders you are willing to forecast, labeled as a forecast.
- The brief includes disclosure, usage rights, and the live URL you will pay on.
- You do not contact a creator until the owner approves the shortlist.

## Workflow

### 1. Score the sheet

Run scripts/calculate_creator_roi.py.

### 2. Read the flags

Open the profile yourself before you defend a high or tiny rate.

### 3. Write the brief

One job, one disclosure line, deliverables, and the usage window.

### 4. Draft outreach

Short, specific, one ask. No fake familiarity.

### 5. Track the deal

Price, expected orders, live URL, paid or not.


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
python3 scripts/calculate_creator_roi.py --help
python3 scripts/calculate_creator_roi.py --self-test
python3 scripts/calculate_creator_roi.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-shortlist` at `0 10 * * 3`: Weekly creator shortlist
- `monday-engagement-vetting` at `0 10 * * 1`: Monday engagement & CPM anomaly check
- `friday-deal-roi-tracker` at `0 14 * * 5`: Friday creator brief & forecasted ROI check

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Creator ROI Vetting
- Sponsor Outreach
- Approval-First
