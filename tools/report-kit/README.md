# AgentScout MCP Server Test Report

HTML + CSS report that prints to a branded, dark-mode PDF. The same builder publishes a noindex web page and the public product page.

Prices and all six Stripe links live only in `data/mcp_test_report.json`. `sell` is `intro` or `full`. The product page and the product feed use that flag. The page sells the MCP server test and the bundle. The AI visibility check links stay in the file until that page exists. Questions still go to support@agentscouthq.com.

## What the harness is allowed to keep

The harness never prints or writes an MCP session id, bearer token, or API key. `harness/redact.py` replaces those values with `[redacted]` before a transcript is printed or saved. The client still holds the session id in memory so the next request can send it.

Do not put session tokens or secrets in the scorecard. Do not commit a transcript you have not checked.

## 1. Probe an endpoint

From `tools/report-kit/harness/`:

```bash
python3 probe_init.py https://example.com/mcp
```

With no arguments it probes the built-in public documentation servers. Output says `session_set=True` or `False`. It does not print the session value.

## 2. Record a transcript

```bash
python3 mcp_http_client.py \
  --url https://example.com/mcp \
  --out /tmp/mcp-transcript.json \
  --runs 5
```

`--out` is required, so a run cannot silently write a transcript somewhere else. The client calls initialize, lists tools, resources, and prompts, then calls a few read-only tools. Names that look like write, send, pay, or delete are refused. Five runs is the sample's latency median.

## 3. Draft the scorecard

```bash
python3 draft_scorecard.py \
  --transcript /tmp/mcp-transcript.json \
  --out /tmp/scorecard.json
```

Latency rows and the endpoint are copied from the transcript. Score, verdict, fixes, methodology, and the plain-English box stay empty. Fill those from the written report. The builder will not invent them. `sample-scorecard.json` in this directory is the filled-in sample.

## 4. Render HTML, PDF, and the badge

From `tools/report-kit/`:

```bash
python3 build_report.py \
  --transcript /tmp/mcp-transcript.json \
  --scorecard /tmp/scorecard.json \
  --html /tmp/report.html \
  --pdf /tmp/report.pdf \
  --badge /tmp/badge.svg
```

`--badge` writes an SVG from the scorecard score and `badge_date`. The words "Tested by AgentScout", the score, and the date are outlined from those values. Chrome headless prints the PDF (`--no-pdf-header-footer`). Letter size, selectable text, embedded Inter.

Optional page images:

```bash
python3 build_report.py \
  --transcript samples/mcp-test-report-sample-2026-11-11.transcript.json \
  --scorecard sample-scorecard.json \
  --html sample.html \
  --pdf /tmp/sample.pdf \
  --badge badge-sample.svg \
  --previews /tmp/previews
```

`--previews` needs `pdftoppm`.

## 5. Publish the site pages

From the repo root:

```bash
python3 tools/report-kit/publish_site.py
```

That command:

- copies the report stylesheet, fonts, and logo to `assets/mcp-report/`
- writes the sample report at `/r/<token>/` from `data/mcp_test_report.json` (24+ character token, `noindex, nofollow`, PDF and badge beside the page)
- writes `/mcp-test-report.html` from the same price file
- keeps `/r/` out of `sitemap.xml`
- adds the product page to the sitemap and the footer / MCP menu

The sample is the only private report linked from a public page. Booking inside a report stays the placeholder already in the scorecard. Do not invent a live booking URL.

## Brand

Colors match the live dark theme (`#0E1015`, `#9393FF` / `#7373ff`, Inter). Static Inter files in `assets/fonts/` are SIL OFL instances so Chrome can embed TrueType outlines.

The badge is a dated test result, not an endorsement.
