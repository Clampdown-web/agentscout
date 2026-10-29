---
name: thirty-day-calendar
description: "Maps buyer questions into a 30-day content calendar across blog, newsletter, YouTube, and social, turning every flagship article or video into 5 channel-ready assets. Use for content strategist work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Content Strategist Agent: 30-day editorial calendars, topic clusters & multi-channel repurposing

This skill trains an assistant to do **content strategist** work for **{{YOUR_COMPANY}}** (Maps buyer questions into a 30-day content calendar across blog, newsletter, YouTube, and social, turning every flagship article or video into 5 channel-ready assets.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "30-day editorial calendars, topic clusters & multi-channel repurposing".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- A pillar owns a cluster. Random topics do not compound.
- Map each piece to a buyer stage so the month is not all 'buy now'.
- Ready-to-buy stays the minority.
- Repurpose after the source piece is good, not before.
- Refresh a page that already earns traffic before you start a cousin URL.
- A brief names the query, the outline, the sources, and the internal links.

## Workflow

### 1. Name the pillars

Three to five. If a sixth appears, it replaces one.

### 2. Generate the month

Run scripts/generate_30day_calendar.py.

### 3. Promote the best four

Those become the pieces with a real brief. The rest stay small.

### 4. Write the repurpose matrix

Post, email, short video, FAQ block.

### 5. Hand the calendar over

{{YOUR_OWNER_NAME}} deletes anything off-brand before production starts.


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
python3 scripts/generate_30day_calendar.py --help
python3 scripts/generate_30day_calendar.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `monthly-calendar` at `0 10 1 * *`: 30-day calendar
- `quarterly-refresh` at `0 10 1 1,4,7,10 *`: Decay and refresh list

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- 30-Day Content Map
- 1-to-5 Repurposer
- Zero Telemetry
