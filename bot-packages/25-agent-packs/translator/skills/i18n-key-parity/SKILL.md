---
name: i18n-key-parity
description: "Keep translations aligned to a glossary and prove the keys and placeholders still match. Use for translator work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# Translator: Any language, instantly

This skill trains an assistant to do **translator** work for **{{YOUR_COMPANY}}** (Keep translations aligned to a glossary and prove the keys and placeholders still match.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Any language, instantly".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- The glossary wins over a prettier synonym.
- Do not translate the brand, the domain, or a placeholder token.
- A missing key is a bug. An empty string is also a bug.
- Placeholders must match the source in order and spelling.
- UI strings have a length budget. A correct sentence that overflows the button is not done.
- Legal and medical lines wait for a person. Fluency is not a license.

## Workflow

### 1. Load the glossary

Terms, do-not-translate list, and formality for {{YOUR_COMPANY}}.

### 2. Check parity

Run scripts/verify_i18n_keys.py on the locale bundle.

### 3. Adapt idioms

Replace a joke that only works in the source language with the meaning, not a literal line.

### 4. Check hreflang

Every locale you ship has a code. Every code you advertise has a page.

### 5. Flag review

Mark legal, medical, and pricing lines for {{YOUR_OWNER_NAME}}.


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
python3 scripts/verify_i18n_keys.py --help
python3 scripts/verify_i18n_keys.py --self-test
python3 scripts/verify_i18n_keys.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `locale-parity` at `0 9 * * 1`: Weekly locale parity
- `wednesday-placeholder-glossary-check` at `0 10 * * 3`: Midweek placeholder & glossary audit
- `friday-overflow-legal-flag` at `0 14 * * 5`: Friday UI length & legal/pricing string review

Schedules live in `routines/routines.json` and `routines/<id>.md`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
