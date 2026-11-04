# Architecture

Source `0668a45610a2bb0d2e0165927d90bb0b36c7d5ce` on `main` (clean). No compatible prior ledger or findings file exists. Profile `standard`. Scope is the whole repository. Budget is unset. Execution is source-and-local only, and this host cannot enforce every required sandbox control (no bubblewrap/nsjail/firejail; `unshare --mount` cannot remount `/proc`). Hunters must not execute target code. A claim that needs a run stays `needs_validation`.

## Product and principals

AgentScout is a public directory of AI tools and MCP servers: generated HTML and JSON, a read-only MCP worker, a votes/roast worker, and a patch for an image/submit worker whose inner program is not in this repo. Visitors read pages, save favorites in `localStorage`, and cast votes. Makers submit listings, reviews, and image prompts. MCP clients call JSON-RPC tools. Operators build the site and hold Cloudflare secrets (`TURNSTILE_SECRET`, `STATS_KEY`, GitHub tokens) outside git. There is no login and no tenant store. Protected resources are vote integrity, the roast fetcher’s network, stats and review-admin routes, Turnstile enforcement, and operator-paid generation.

Comparable baseline, from in-repo docs only: a public MCP registry (schema `2025-09-29` in `cloudflare-mcp-worker/worker.js`) plus a static directory. Public read-only catalog data is an accepted trade-off. It does not excuse a broken fetcher, secret compare, or bot check.

## Stack and deploy paths

Python generators (`build_site.py` and `build_*.py`) write the Pages/GitHub Pages tree. Node workers: `cloudflare-api-worker/src/worker.js` (`votes.agentscouthq.com`, KV `VOTES`), `cloudflare-mcp-worker/worker.js` (rate-limit bindings; two wrangler names), and `cloudflare-image-worker-patches/security.js` wrapped by `entry.js` around a missing `index.js`. `_headers` sets HSTS and a report-only CSP; pages also carry a meta CSP. No `.github` workflows. Offline tests exist under `cloudflare-api-worker/test/`, `cloudflare-mcp-worker/test/`, `cloudflare-image-worker-patches/security.test.mjs`, and `free_tools_js/escape.test.mjs`. They were not run.

## Entries and trust boundaries

Anonymous `GET|POST /roast` fetches a caller URL after `ssrf.js`, then `origin/llms.txt`, with an 8s cap, 512KB cap, and three manual redirects. `POST /vote` allows only the site Origin or Referer, then hashes salt, `CF-Connecting-IP` (or `X-Forwarded-For`), and slug into KV. `GET /votes` is public. MCP `POST` is unauthenticated JSON-RPC over a fixed snapshot, CORS `*`, with a verified-bot rate-limit exemption. The image patch origin-gates and rate-limits `/submit`, `/review`, and `/reviews*`; compares `X-Stats-Key` with `safeEq`; and siteverify’s `POST /submit` and `POST /generate` only when `TURNSTILE_ENABLED` is `true`. `entry.js` then forces that flag to `false` for the inner worker. `/track`, `/readiness`, `/geo`, and `/share` are not gated here. Browsers render catalog JSON and a few URL or hash fields into the DOM. Build scripts fetch operator-supplied URLs.

Strongest source-visible control on each boundary: `isBlockedIp` plus DoH answers for roast; `voteAllowed` for votes; `postAllowed`, `safeEq`, and siteverify for the patch; schema checks and rate limits for MCP; `esc` / `ASe` for the DOM. Platform facts not in source (live Turnstile flag, inner `index.js`, whether Cloudflare always sets `CF-Connecting-IP`, Workers’ private-address fetch policy, which MCP wrangler file is deployed) are not assumed.

## Starting points

`cloudflare-api-worker/src/worker.js`, `ssrf.js`, `score.js`; `cloudflare-mcp-worker/worker.js`; `cloudflare-image-worker-patches/security.js`, `entry.js`; `app.js`, `reviews.js`, `quiz.js`, `generate.js`, `consent.js`, `track.js`, `share.js`, `free_tools_js/`; `submit.html`; `_headers`, `_redirects`; `build_site.py`, `build_seo_new.py`, `scripts/add_tools.py`, `scripts/check_mcp_links.py`, `scripts/sponsor_stats.py`.

## Coverage consequences

Nothing is carried forward and nothing is excluded as a prior confirmation. Inner image-worker behavior, SSE at `agentscouthq.com/mcp/sse`, and dashboard bindings stay explicit gaps.

## Companions

Selected because the boundary is present, not because a product name appears: `WEB-PROTOCOL-AND-AUTH.md` (Origin, Referer, forwarded client IP, API key compare, cache headers); `CLIENT-SIDE.md` (DOM and `localStorage`); `AI-AND-LLM.md` and `PROTOCOLS-RPC-AND-MESSAGING.md` (MCP JSON-RPC tools); `CLOUD-AND-DEPLOYMENT.md` (Workers, KV, wrangler vars); `RESOURCE-EXHAUSTION-AND-AVAILABILITY.md` (roast and `/generate` cost); `SUPPLY-CHAIN-AND-RELEASE.md` (Python deps and build inputs). Not selected: `MEMORY-SAFETY-AND-BINARY.md` (no unsafe native code), `DESKTOP-MOBILE-AND-LOCAL-IPC.md` (no local IPC), `DATA-ISOLATION-AND-LIFECYCLE.md` (no tenant store).
