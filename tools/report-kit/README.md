# AgentScout MCP Server Test Report template

HTML + CSS report that prints to a branded, dark-mode PDF. The same files can be served as an on-site report page.

## Build the sample

From this directory:

```bash
python3 build_report.py \
  --transcript ../mcp-test-report-sample-2026-11-11.transcript.json \
  --scorecard sample-scorecard.json \
  --html sample.html \
  --pdf ../mcp-test-report-sample-2026-11-11.pdf \
  --badge badge-sample.svg \
  --previews previews \
  --preview-prefix ../mcp-test-report-sample-2026-11-11
```

`--previews` rasterizes every PDF page to `previews/page-N.png` with `pdftoppm`. `--preview-prefix` also copies them to `PREFIX-page-N.png` beside the PDF and deletes any leftover page PNGs beyond the new count.

## Inputs

- **Transcript JSON** — protocol timings, tool schemas, call results, and HTTP statuses. Latency numbers and pass rates are computed only from this file.
- **Scorecard JSON** — qualitative score (90/100), area points, verdict, top fixes, methodology, and disclaimer. Also holds reusable copy for the cover key-findings effort labels, the plain-English “What this means for you” box, the badge date and disclaimer, and the free-retest next-step text. These come from the written report, not invented by the builder.

Do not put session tokens or secrets in the scorecard. The builder never prints `mcp-session-id` values.

## Brand

Colors, type, and logo match the live AgentScout dark theme (`#0E1015` background, `#9393FF` / `#7373ff` accent, Inter). Static Inter TTF files in `assets/fonts/` were instantiated from Inter variable (SIL OFL) so Chrome embeds real TrueType outlines in the PDF.

The embeddable `badge-sample.svg` is a dark neon “Tested by AgentScout · score · date” mark with outlined Inter text. It is a dated test result, not an endorsement. In the report, the copy-paste HTML and Markdown snippets link to the public AgentScout listing. The badge image URL and the retest booking path are labeled as launch placeholders; do not invent live URL paths that do not exist yet.

## Output

Letter size, selectable text, embedded fonts. Chrome headless is the print engine (`--no-pdf-header-footer`). Page count is computed from the generated sheets (cover with key findings, summary, charts, checks, tools, fixes, badge, methodology with next-step CTA, appendix of exact latency figures).
