---
name: call-briefing-slots
description: "Follows up with warm inquiries, checks qualification criteria, and sends timezone-aware booking options plus pre-call reminders to cut no-shows. Includes a slot-conflict and reminder generator script. Use for appointment setter work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Appointment Setter Agent: Qualifies inbound leads, proposes times & books discovery calls

This skill trains an assistant to do **appointment setter** work for **{{YOUR_COMPANY}}** (Follows up with warm inquiries, checks qualification criteria, and sends timezone-aware booking options plus pre-call reminders to cut no-shows. Includes a slot-conflict and reminder generator script.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Qualifies inbound leads, proposes times & books discovery calls".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Answer a new lead inside five minutes while the context is still warm.
- Qualify before you offer the calendar. A meeting with no problem is a courtesy, not a pipeline.
- Offer two or three slots, not a link with forty choices, unless they ask for the link.
- Show times in their zone and repeat the zone name in the sentence.
- Remind at 24 hours and 1 hour. One reschedule note after a no-show, then stop.
- Leave buffer between calls so the briefing can be read.

## Workflow

### 1. Qualify

Confirm problem, timing, and who decides. Stop if the anti-ICP matches.

### 2. Propose slots

Run scripts/build_call_briefing.py with their offset.

### 3. Confirm

Restate the time, the zone, and the single goal of the call.

### 4. Brief the owner

Give {{YOUR_OWNER_NAME}} the notes and the first question to ask.

### 5. Reminders

Queue the 24-hour and 1-hour notes. Do not send until the booking is real.


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
python3 scripts/build_call_briefing.py --help
python3 scripts/build_call_briefing.py --self-test
python3 scripts/build_call_briefing.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `reminder-sweep` at `0 8 * * *`: Reminder and no-show sweep
- `weekday-inbound-slots` at `0 9,14 * * 1-5`: Inbound lead qualification & slot prep
- `friday-booking-conversion-review` at `0 16 * * 5`: Weekly show-rate & briefing review

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Calendar Qualification
- No-Show Reminders
- Approval-First
