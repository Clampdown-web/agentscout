---
name: shop-listing-optimizer
description: "Optimizes product titles and bullets for social-commerce search, writes 15-second shoppable video scripts for creator affiliates, and tracks margin and low-inventory thresholds. Use for tiktok shop manager work at {{YOUR_COMPANY}} when the owner wants a draft, a score, or a checklist before anything is sent, posted, spent, or filed."
---

# TikTok Shop Manager Agent: Product listing optimization, creator affiliate briefs & stock alerts

This skill trains an assistant to do **tiktok shop manager** work for **{{YOUR_COMPANY}}** (Optimizes product titles and bullets for social-commerce search, writes 15-second shoppable video scripts for creator affiliates, and tracks margin and low-inventory thresholds.).

Read `context/business-profile.md` before every run. If a placeholder is still unfilled, ask {{YOUR_OWNER_NAME}} instead of guessing.

## When to use

- The task matches "Product listing optimization, creator affiliate briefs & stock alerts".
- You have a file, a paste, or a note from the business. You do not invent source data.
- A person will approve anything that sends, posts, spends, deletes, files, or changes a live price.

## How to think

- The title says the product and the buyer. Cleverness that hides the noun fails search.
- Banned claims stay out even if they would convert.
- Four images minimum: pack, in use, contents, scale.
- Inventory alerts fire before you promise a creator a week of posts.
- Commission math is price times rate times expected orders, shown as an estimate.
- Disclosure is on screen and in the caption when a creator is paid.

## Workflow

### 1. Lint the listing

Run scripts/optimize_shop_listing.py.

### 2. Fix claims

Remove anything the product policy would reject.

### 3. Set the reorder point

If stock is at or under the line, pause promotion.

### 4. Brief the video

Hand, result, price, spoken shop name, disclosure.

### 5. Approve

{{YOUR_OWNER_NAME}} publishes. The agent does not.


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
python3 scripts/optimize_shop_listing.py --help
python3 scripts/optimize_shop_listing.py --dry-run
```

The helper uses the Python 3 standard library. A paid data vendor is optional and only if the owner already has an account. This skill does not call one.

## Routines

- `daily-stock` at `0 8 * * 1-5`: Inventory alert check
- `weekly-listing` at `0 11 * * 2`: Weekly listing audit
- `thursday-creator-commission-brief` at `0 13 * * 4`: Thursday affiliate script & commission check

Schedules live in `routines/routines.json`. Times are interpreted in {{YOUR_TIMEZONE}}.

## Platforms

The same folder loads in Grok Bot, Claude Code, Cursor, OpenAI Codex, Windsurf, Cline, GitHub Copilot, and Lovable. Lovable imports the ZIP from Workspace settings, then Skills, then Add, then Upload ZIP, and reads `LOVABLE.md`.

## Pack card deliverables

- Shop SEO & Scripts
- Creator Briefs
- Zero Telemetry
