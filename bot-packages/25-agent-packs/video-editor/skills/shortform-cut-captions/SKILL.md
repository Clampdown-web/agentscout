---
name: shortform-cut-captions
description: "Turn a transcript into captions, a silence cut list, and a 9:16 storyboard. Use for video editor work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Video Editor: Cuts reels and shorts

This skill trains an assistant to do **video editor** work for **{{YOUR_COMPANY}}** (Turn a transcript into captions, a silence cut list, and a 9:16 storyboard.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Cuts reels and shorts".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- The first three seconds must contain a change, a number, or a question. A logo card does not count.
- Cut filler words and dead air. Keep the breath that makes a sentence human.
- Captions are a script, not a dump of every false start.
- Burned-in captions stay inside the safe center so interface buttons do not cover them.
- Music needs a license note. Silence is better than a track you cannot name.
- One video, one job. Do not hide a second offer in the last second.

## Workflow

### 1. Mark the hook

Read the opening three seconds. If it is a greeting, rewrite the first line before you edit.

### 2. Build captions

Run scripts/format_captions_and_cuts.py to emit SRT, VTT, and the gap list.

### 3. Write the cut list

Hand the ffmpeg hint to the editor. Do not render on a machine you have not been given.

### 4. Storyboard 9:16

Three beats: interrupt, proof, next step. Note the on-screen text for each.

### 5. Thumbnail brief

One face or one object, four words or fewer, high contrast.


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
python3 scripts/format_captions_and_cuts.py --help
python3 scripts/format_captions_and_cuts.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `caption-pass` at `0 15 * * 1-5`: Weekday caption pass

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
