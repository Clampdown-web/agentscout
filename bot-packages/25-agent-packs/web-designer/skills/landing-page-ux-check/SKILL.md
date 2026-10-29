---
name: landing-page-ux-check
description: "Designs high-converting landing page sections, checks 360px/768px/1280px responsive layouts for zero horizontal overflow, and verifies WCAG contrast across dark and light themes. Use for web designer work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Web Designer Agent: Responsive landing pages, mobile UX audits & dark/light CSS polish

This skill trains an assistant to do **web designer** work for **{{YOUR_COMPANY}}** (Designs high-converting landing page sections, checks 360px/768px/1280px responsive layouts for zero horizontal overflow, and verifies WCAG contrast across dark and light themes.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Responsive landing pages, mobile UX audits & dark/light CSS polish".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- Pick a type and a color on purpose. A generic purple gradient is not a brand.
- The first screen holds one promise, one proof, and one button.
- 360px and 390px must not scroll sideways.
- Text contrast aims for 4.5 against its background.
- Fixed pixel widths wider than the phone are a bug, not a look.
- Empty image alts fail the page even if the picture is pretty.

## Workflow

### 1. Sketch the sections

Hero, proof, offer, objections, final button. Name what each section must do.

### 2. Check the file

Run scripts/check_landing_page_ux.py on the HTML.

### 3. Fix overflow

Replace fixed widths with a fluid layout. Recheck 360 and 390.

### 4. Fix contrast

Darken or lighten until the pair clears 4.5 for body text.

### 5. Hand off

List remaining issues. Do not deploy.


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
python3 scripts/check_landing_page_ux.py --help
python3 scripts/check_landing_page_ux.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `page-check` at `0 14 * * 3`: Landing page UX check
- `monday-mobile-viewport-audit` at `0 10 * * 1`: Monday 360px/390px mobile overflow audit
- `friday-cta-contrast-review` at `0 15 * * 5`: Friday above-the-fold CTA & contrast check

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Responsive UI Audit
- Dark/Light Contrast
- Zero Telemetry
