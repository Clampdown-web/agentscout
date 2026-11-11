# AgentScout AI Visibility Check template

HTML + CSS report that prints to a branded, dark-mode PDF. The look matches the MCP Server Test Report: dark neon AgentScout theme, a cover with a Key findings box, a plain-English “What this means for you” box, charts, top fixes, a next-step retest, methodology, disclaimer, and an appendix.

This folder builds a report from dated captures. Publishing the public page is a separate command, below. Do not edit `../report.css` or `../build_report.py`; those are the indigo MCP report.

## Build the sample

From this directory:

```bash
python3 build_report.py \
  --captures captures.json \
  --scorecard sample-scorecard.json \
  --html sample.html \
  --pdf ../ai-visibility-check-sample-2026-11-11.pdf \
  --previews previews \
  --preview-prefix ../ai-visibility-check-sample-2026-11-11
```

`--previews` rasterizes every PDF page to `previews/page-N.png` with `pdftoppm` at 150 dpi (about 1,275 px wide, comfortable on a phone in chat). `--preview-prefix` also copies them to `PREFIX-page-N.png` beside the PDF and deletes any leftover page PNGs beyond the new count.

## How to rerun this for a customer site

1. **Write the prompt list.** About ten questions a real buyer or maker would type. Mix category, problem, comparison, and one brand query. Mark up to five as top prompts. Do not pad the list with vanity queries.
2. **Pick three or four real rivals** that buyers might also be sent to. Use each rival’s public name and URL. Do not invent a competitor.
3. **Run every prompt** on the answer surfaces you can reach without signing in anywhere new: web search results and AI-answer style search (WebSearch). If the customer pastes a ChatGPT, Claude, Gemini, or Perplexity answer, include that paste as its own dated capture. Label any surface you could not run as not run.
4. **Save a dated capture** of each answer into `captures.json`: the prompt, kind, date (America/Los_Angeles), synthesis, source URLs, and any third-party pages you opened. Copy this sample file and replace the records. Do not invent a result.
5. **Score** the customer site and each rival on each prompt with one rung: recommended > cited > mentioned > absent. Use the definitions in the scorecard (and in the sample report). Be conservative. A product that is only the subject of the query is mentioned, not recommended. Same-name collisions must be checked and noted.
6. **Citation audit.** Open the main third-party pages the answers cited. Note which ones already name the customer, and which are realistic places to get listed or mentioned.
7. **Fill `sample-scorecard.json`** (or a customer-named copy) with the area scores, verdict, “what this means for you” copy, top fixes, methodology, and disclaimer. The 100-point method is documented in that file:
   - Category discovery (30)
   - Problem and how-to queries (28)
   - Comparison queries (16)
   - Brand search (10)
   - Third-party citations (16) — the customer’s own pages do not count
8. **Build** with `build_report.py` as above, pointing `--captures`, `--scorecard`, `--html`, `--pdf`, and `--previews` at the customer files. Always also produce page PNGs; some phones cannot preview the PDF in chat.
9. **Do not publish, email, or change the customer’s site** as part of the check. The booking link on the next-step page stays a clearly marked placeholder until a live path exists.

## Inputs

- **Captures JSON** — every prompt, the dated answer, source links, pages opened, and the rung for the subject and each rival. Presence, share of answer, and the appendix log are computed only from this file.
- **Scorecard JSON** — the 100-point area scores, verdict, key-findings copy, fixes, methodology, and disclaimer. These come from the written report, not invented by the builder.

Do not put session tokens or secrets in either file.

## Brand

This report uses a high-contrast near-black theme, distinct from the MCP Server Test Report's indigo on `#0E1015`. The page is a flat `#0A0A0B`, cards are `#151517` with `#2A2A2E` borders, and body text is `#F5F5F5`. Muted text is no dimmer than `#C4C4C8`. Accents, the score ring, chips, numbered badges, links and the wordmark's “Scout” use warm orange `#FF8A3D` / `#FF9F43`, with dark `#0A0A0B` text on orange fills. Warn is `#FACC15` so it stays distinct from the orange accent. Pass and fail remain `#34d399` and `#F87171`. Body type is 12pt with a 1.55 line height; labels are at least 11px. Static Inter TTF files in `assets/fonts/` were instantiated from Inter variable (SIL OFL) so Chrome embeds real TrueType outlines in the PDF.

The next-step booking path is labeled as a launch placeholder; do not invent a live URL path that does not exist yet. Shown prices are not required in the report.

## Publish the sample on the site

From the repo root:

```bash
python3 tools/report-kit/publish_visibility.py
```

Prices and Stripe links are read only from `data/ai_visibility_check.json`. `sell` is `intro` or `full`. The public page shows the intro buttons while `sell` is `intro`. The full-price links stay in that file. The command writes:

- `ai-visibility-check.html` (in the sitemap)
- `/r/<sample_slug>/` with `noindex, nofollow`, plus `report.pdf` rendered from this template
- page previews under `assets/ai-visibility-report/previews/`
- the “AI visibility check” link beside “MCP server test” in the shared nav and footer

`sample_slug` in the price file is the private path. Keep that name. Do not rename it to a token.

## Output

Letter size, selectable text, embedded fonts. Chrome headless is the print engine (`--no-pdf-header-footer`). Page count is computed from the generated sheets (cover with key findings, summary, share-of-answer charts, per-question table, prompt notes, citation audit, top fixes, methodology with next-step CTA, appendix of the prompt log).
