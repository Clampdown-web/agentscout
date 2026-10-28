---
name: seo-aeo-site-audit
description: "Audit findability for humans and answer engines: titles, schema, internal links, and a plain llms.txt plan. Use for seo specialist work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# SEO Specialist: Gets you ranking on Google

This skill trains an assistant to do **seo specialist** work for **{{YOUR_COMPANY}}** (Audit findability for humans and answer engines: titles, schema, internal links, and a plain llms.txt plan.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Gets you ranking on Google".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- One page, one query family. Two URLs chasing the same query need a canonical decision.
- Title and H1 may rhyme. They should not be copies if the title can carry the specific modifier.
- JSON-LD must match the visible name, price, and organization.
- Answer the question in the first screen if you want an answer engine to quote you.
- Internal links use the words a buyer would type, not 'click here'.
- Do not invent Core Web Vitals. Say 'not measured' until field data exists.

## Workflow

### 1. Crawl the file you have

Run scripts/seo_site_audit.py on a saved page or one URL {{YOUR_OWNER_NAME}} names.

### 2. Fix the index basics

Title length, meta description, single H1, canonical, and image alts come first.

### 3. Check the entity

Organization or product JSON-LD uses the same name as the page heading.

### 4. Map queries to pages

List the query, the URL, and any second URL that competes with it.

### 5. Write llms.txt notes

List the pages a model may quote and the pages it should skip.

### 6. Local NAP

If the business has a location, name, address, and phone must match the profile.


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
python3 scripts/seo_site_audit.py --help
python3 scripts/seo_site_audit.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `weekly-seo-crawl` at `0 7 * * 1`: Weekly SEO and AEO audit
- `monthly-query-map` at `0 8 1 * *`: Monthly query map

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.
