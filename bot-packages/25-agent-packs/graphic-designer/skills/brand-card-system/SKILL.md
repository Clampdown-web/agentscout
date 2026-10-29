---
name: brand-card-system
description: "Generates on-brand creative briefs, layout specs, contrast-checked color palettes, and image prompts for ads, social posts, and thumbnails. Ships with an automated brand-asset linter and multi-aspect export checklist. Use for graphic designer work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Graphic Designer Agent: High-converting ad creatives, social graphics & YouTube thumbnails

This skill trains an assistant to do **graphic designer** work for **{{YOUR_COMPANY}}** (Generates on-brand creative briefs, layout specs, contrast-checked color palettes, and image prompts for ads, social posts, and thumbnails. Ships with an automated brand-asset linter and multi-aspect export checklist.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "High-converting ad creatives, social graphics & YouTube thumbnails".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- One accent color does the pointing. A second accent is noise.
- Headline under eight words. Brand name is a signature, not a second headline.
- Check ink against background before you export. Aim for a 4.5 contrast ratio on text.
- Design the 9:16 story and the 1.91:1 link card from the same tokens, not as unrelated pictures.
- Leave a quiet edge of at least 64px so a platform crop does not eat the offer.
- Write the image-model prompt after the layout is decided, so the prompt serves the design.

## Workflow

### 1. Capture the kit

Record hex colors, display font, text font, and logo clear-space for {{YOUR_COMPANY}} in context/business-profile.md.

### 2. Emit the spec

Run scripts/generate_brand_card_spec.py. Read the contrast pairs before you approve a background.

### 3. Pick the ratio

Choose feed portrait, story, landscape ad, or thumbnail. Do not stretch one file into all four.

### 4. Write three concepts

Each concept gets a one-sentence rationale: what the eye hits first and why.

### 5. Export checklist

Confirm safe margins, readable type at phone size, and a file name that includes the ratio.


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
python3 scripts/generate_brand_card_spec.py --help
python3 scripts/generate_brand_card_spec.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-asset-batch` at `0 10 * * 2`: Weekly social asset batch

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Ad & Thumbnail Specs
- WCAG Contrast Check
- Zero Telemetry
