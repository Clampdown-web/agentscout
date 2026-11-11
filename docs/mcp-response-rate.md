# MCP response rate

The daily link check answers a different question from this probe. `scripts/check_mcp_links.py` requests each MCP listing’s website and GitHub URL with HTTP HEAD, then GET, and writes `data/mcp_link_status.json`. `build_aicite.py` (`mcp_reachability`) and `build_status.py` turn that file into the “checked servers live” line on `/mcp/`, `llms.txt`, and `status.json`. That work landed in PR #97 (`0768c85d`, “Cite the daily MCP reachability check for AI answers”). A live homepage is not an MCP handshake.

`api/products.json` is the paid catalog (packages, add-ons, bot templates, agent packs, reports). `scripts/publish_gate.py` checks that `cloudflare-mcp-worker/products_snapshot.json` matches it byte for byte. It is not the MCP directory. The directory is `tools.json`. Rich endpoint notes, when a listing has them, are `tool_rich.json` → `mcp.endpoint` and `mcp.transport`.

There is no GitHub Actions schedule for the link check. `.github/workflows/production-smoke.yml` only GETs the live site. This probe is a separate daily workflow so that smoke job stays read-only.

## 1. Probe

`scripts/mcp_response_rate.py` classifies every `tools.json` row whose category is `MCP servers`.

A server is **remote** when we already have a public `http` or `https` endpoint:

- `tool_rich.json` `mcp.endpoint`, when the value is an `http` or `https` URL. A non-HTTP endpoint (stdio, `npx`, a local command) is **local only**.
- Otherwise a unique match against the public registry at `registry.modelcontextprotocol.io` (`version=latest`). The join is an exact website URL (`url` or `website` vs `websiteUrl`, query and fragment ignored) or an exact `owner/repo` GitHub path. If two registry rows or two listings share that key, the join is dropped. A shared repo such as `modelcontextprotocol/registry` must not attach someone else’s remote to our MCP Registry listing.
- Registry `remotes[]` of type `streamable-http` or `sse`. A `{var}` in the URL is filled only from that remote’s default. Streamable HTTP wins over SSE when both are concrete. The URL is screened with the same public-address rule as `scripts/check_mcp_links.py` (`public`): private, loopback, link-local, and metadata addresses are not requested.

A unique match whose packages are stdio and which has no concrete remote is **local only**. Anything else stays unclassified. Unclassified is “Not yet checked”, not a failure. Local-only servers are not requested and are not counted as down.

For each remote server the probe sends only:

1. JSON-RPC `initialize` (`protocolVersion` `2025-06-18`, client `AgentScoutBot` 1.0, empty capabilities). One retry if the server reports a different supported protocol version.
2. The `notifications/initialized` notification. That is the handshake, not a tool call.
3. `tools/list` with no arguments.

`tools/call` is not a permitted method. The client refuses any other method before it touches the network. No tool is invoked, including read-only tools.

Request headers: `Accept: application/json, text/event-stream`, `Content-Type: application/json`, `User-Agent: AgentScoutBot/1.0 (+https://agentscouthq.com)`, `Origin: https://agentscouthq.com`, and `MCP-Protocol-Version`. `Mcp-Session-Id` is echoed when the server sets it and is not written to disk. No `Authorization` header and no environment credentials. A query string that looks like an API key, token, secret, or password is skipped and not stored.

Streamable HTTP is a POST. The body may be JSON or an SSE `event: message` payload. SSE opens the event stream, reads the `endpoint` event, and POSTs the same JSON-RPC there. Redirects are followed only while every hop stays public, and stop at a non-public target.

Each attempt records: pass/fail outcome, HTTP status, latency (milliseconds, all requests in the attempt), protocol version, tool count, and a reason. Outcomes:

| Outcome | Meaning |
| --- | --- |
| `responded` | `initialize` returned a `protocolVersion` and `tools/list` returned a `tools` array (empty is fine). |
| `needs_auth` | HTTP 401 or 403, or a JSON-RPC error that says authentication is required. This is not “down”. |
| `failed` | Anything else we could not treat as MCP. |

Reason categories: `timeout`, `auth`, `not_mcp`, `tls`, `dns`, `http_5xx`, `http_4xx`, `protocol` (JSON-RPC error that is not auth), `connection`, `non_public` (we refused the address or a redirect). Timeout is 10 seconds per request. Politeness: about 5 requests per second across the whole run, at most one request per second to a single host, and at most 8 servers per host in one run. Extra servers on a busy host are deferred to a later day instead of being marked down.

The registry walk stops at 1,200 pages (100 servers each) or at the end cursor, whichever comes first. A run that hits the cap still probes the matches it has and does not delete local-only rows from the summary. The daily job probes at most 200 remote servers. `data/mcp-health/state.json` stores the next slug and any host-capped deferrals so the slice rotates. Local-only rows are refreshed from the classification and are not part of that 200.

## 2. Storage

Append-only history is `data/mcp-health/YYYY-MM.jsonl`, one JSON object per line, no response body, no tool names, no session id:

```json
{"endpoint":"https://example.com/mcp","http_status":200,"latency_ms":180,"outcome":"responded","protocol_version":"2025-06-18","reason":null,"slug":"example","tool_count":3,"transport":"streamable-http","ts":"2026-11-11T15:15:02Z"}
```

Timestamps are UTC. A month at 200 probes a day is on the order of 1–2 MB, which GitHub Pages can serve. The script does not delete old months. If a file grows past a few megabytes, drop months older than 90 days in a later change; the summary is rebuilt from whatever lines remain.

`data/mcp-health/summary.json` is derived. For each remote slug it stores probe count, last checked, last success, last outcome, and 7-day and 30-day counts. The response rate denominator is `responded` plus `failed` in that window. `needs_auth` is excluded, so an auth wall does not lower the rate. `rate_7d` and `rate_30d` are the responded share of that denominator, rounded to three decimals. Local-only rows are `{disposition, display, probes}` only.

`display` is what a page is allowed to say:

| `display` | Badge |
| --- | --- |
| `rate` | `Responded {ok_30d}/{n_30d} checks in last 30 days` |
| `needs_auth` | `Needs auth` |
| `local_only` | `Local only` |
| `insufficient` | `Not yet checked` |

`rate` requires at least 3 probes in the last 30 days that are responded or failed. `needs_auth` requires at least 3 probes in the window and no successful handshake (every probe was auth, or auth never cleared the 3-probe bar for a rate). Fewer than 3 probes is `insufficient`. Missing from the summary means the same thing: not yet checked. `badge_text()` in the script is the only wording phase 2 should print.

A partial registry download does not delete local-only rows already in the summary. A complete download replaces them.

## 3. Display (not in this change)

Badges and ranking are not wired into HTML here. Tool pages, `categories/mcp-servers.html`, and the ranked MCP lists are generated (`build_rich.py`, `build_mcp_tasks.py`, `build_best.py`, and the category build). This checkout has `categories/mcp-servers.html` and no `mcp-servers-p2`…`p21` files. Rebuilding those pages, or bumping `ASSET_V` in `build_tasks.py` (the `styles.css?v=` / `app.js?v=` cache-buster), would rewrite the static site. That stays a follow-up.

When it lands:

- On each `tools/{slug}.html`, a badge in the existing `.badges` / `.b` style, using `badge_text()`. No percentage and no “down” when `display` is `insufficient`.
- On `/mcp/` task lists and `best/mcp-servers*.html`, a “Responds” sort that only orders servers whose `display` is `rate`, by `rate_30d` then `n_30d`. Everyone else keeps today’s order (GitHub stars, then ratings, then recent push, then maturity in `build_mcp_tasks.py`). A thin sample must not jump the list.
- Do not rewrite the PR #97 reachability sentence. Link-check “live” and MCP “responded” stay separate facts.
- If CSS is added, bump `ASSET_V` and regenerate the `?v=` stamps. Do not weaken CSP or Turnstile.

`summary.json` is the input. Absence of a slug is “Not yet checked”.

## 4. Schedule

`.github/workflows/mcp-response-rate.yml` runs at 15:15 UTC (7:15 AM Pacific during standard time, 8:15 AM during daylight time) and on `workflow_dispatch`. It checks out the repo, runs:

```bash
python3 scripts/mcp_response_rate.py --limit 200
```

and commits only `data/mcp-health/` as `github-actions[bot]`. No secrets, no deploy, no Cloudflare worker changes. The link-check script is unchanged.

### Run locally

From the repo root, with network access:

```bash
python3 scripts/mcp_response_rate.py --limit 20 --dry-run
python3 scripts/mcp_response_rate.py --limit 200
```

`--dry-run` performs the handshakes and prints counts. It does not write history. Omit `--dry-run` to append `data/mcp-health/YYYY-MM.jsonl`, rebuild `summary.json`, and advance `state.json`. Tests use a local mock server and do not open the network:

```bash
python3 scripts/test_mcp_response_rate.py
```
