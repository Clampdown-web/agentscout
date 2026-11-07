# Security rollback and incident notes

This is the operator note for the production-hardening branch. It does not deploy anything. Merging it does not publish a Worker. The staged plan, the captured image-worker hashes, and the hostname caveat are in `docs/recovery-plan.md`. `cloudflare-image-worker-patches/` is the drop-in guard. Someone still has to copy it into the image project and deploy that project on purpose.

No catalog builder, news builder, or SEO builder is changed here. `daily_update.py`, `build_site.py`, and the other `build_*.py` scripts stay as they are, so the daily catalog build and the existing SEO generation limits stay as they are.

## Rollback

- Static site: this change does not edit HTML, `_headers`, `_redirects`, or generated pages. The report-only Content Security Policy stays report-only. Do not switch that header to an enforcing policy in a hurry. Pages ship inline scripts, and a static header cannot add a per-response nonce. Google Analytics, Beehiiv, and Turnstile would need an explicit allowlist pass first.
- Image worker: if a deploy of `security.js` / `entry.js` misbehaves, roll that Worker back from the Cloudflare dashboard (Workers, the `agentscout-image` service, Deployments, previous version). Do not `wrangler deploy` it from this repository. Turning `TURNSTILE_ENABLED` off makes `/submit` and `/generate` skip siteverify. Prefer the previous deployment.
- Symptom that means the single-use token was checked twice: real visitors with a fresh widget token get `403` `Bot check failed.` on `/submit` or `/generate`, while the dashboard shows `TURNSTILE_ENABLED` is `true`. `protect()` hides that flag from the inner handler on those two POSTs, and `entry.js` hides it again. Roll back rather than clearing the flag.
- `/readiness` starts returning `400` for a site you know is public: DNS lookup failed, or the answer had no A/AAAA address. Roll back the image worker. Do not delete the check on the server.
- Votes worker: roll back that Worker's previous deployment the same way. The KV counter is serialized inside one isolate only. `ROAST_RL` and `VOTE_RL` apply only after those bindings exist. This branch does not create them. A missing `VOTES` binding returns `503` either way. The capture of the image worker did not prove which hostname reaches which script.
- GitHub Actions: `.github/workflows/security.yml` only checks out the repo, runs the offline `node --test` files, and runs `pip-audit` against `requirements.txt`. It has `contents: read`, no secrets, and no deploy step. Delete or disable the workflow to stop it.

## While something is wrong

Do not paste `TURNSTILE_SECRET`, `STATS_KEY`, Turnstile tokens, or request bodies into an issue, a log line, or a chat. The public Turnstile site key is already in `reviews.js` and `generate.js`. The secret is not.

- Widespread `403` on admin paths (`/reviews/pending`, `/reviews/admin`, `/stats`, `/trending/stats`): the `X-Stats-Key` header does not match `STATS_KEY`, or the binding is missing. Missing fails closed. Do not log the header.
- `503` `Rate limiting is not configured.` on the image worker: `IMAGE_READ` or `IMAGE_WRITE` is missing. On the MCP worker: `MCP_BURST` or `MCP_MINUTE` is missing. Fix the binding, do not remove the check.
- `429` on submit or generate: the write cap is 10 requests per 60 seconds per `CF-Connecting-IP`, per Cloudflare location. That is the limiter, not an outage.
- Suspected secret in a log or a commit: rotate that secret in the Cloudflare dashboard, update the Worker binding, and redeploy that Worker. Do not put the new value in git. Rotation is a human step; this repository does not do it.

## Checks this repository cannot prove

Confirm these in the Cloudflare and GitHub dashboards before treating production as patched.

1. Version `1c6368ca-f9d5-403e-92c2-7954641c2153` was captured. It matches the pre-change guard, not this branch. A later dashboard edit can diverge again. Hostname routing was not in that capture.
2. `TURNSTILE_ENABLED` on that Worker is the string `true`. `TURNSTILE_SECRET` is set and is the secret for the site key already on the site. If the var is anything else, `/submit` and `/generate` skip siteverify. Origin checks and `IMAGE_WRITE` still apply.
3. `STATS_KEY` is set. Prove it with one authenticated request that expects `200`, not by printing the value.
4. Rate-limit namespace ids are unique in the account: image `IMAGE_WRITE` `481201`, `IMAGE_READ` `481202`; MCP `MCP_BURST` `481015`, `MCP_MINUTE` `481060`. `cloudflare-mcp-worker/wrangler.toml` names the script `agentscout-mcp-registry`. `wrangler.jsonc` names it `agentscout-mcp` and has no route. Confirm which script `mcp.agentscouthq.com` actually runs.
5. The KV id in `cloudflare-api-worker/wrangler.toml` is an identifier, not a credential. Confirm the deployed votes module matches `src/worker.js` before relying on it. Do not infer hostnames from this repo.
6. Worker logs do not contain tokens, `STATS_KEY`, or `TURNSTILE_SECRET`. The MCP logger in git records method, path, status, the RPC method name, and `error.message` only.
7. Pages still sends `Content-Security-Policy-Report-Only`. That is a defense-in-depth gap. It is not, by itself, a demonstrated exploit, and it is not fixed by flipping the header to enforce.
8. GitHub Dependabot alerts are enabled for the repository. This adds `.github/dependabot.yml`. The setting is still a dashboard switch. There is no npm manifest; the Python pins are `requirements.txt`.
9. Off-box backups and a tested restore are not in git. Stripe Payment Links on the site are public URLs. Webhook fulfillment is not in this repository.

## Known limits that this pass does not close

- `POST /review` is origin-checked and rate-limited here. It is not siteverified here. The captured inner handler siteverifies only when `REVIEW_TURNSTILE` is the string `true`. That value was not read. Doing it in both places would spend the token twice. See `docs/recovery-plan.md`.
- Stats-key paths are `/reviews/pending`, `/reviews/admin`, `/reviews/export`, `/stats`, and `/trending/stats`. The captured inner router does not expose a deeper admin path. `/review/moderate` is an HMAC link, not a stats-key route.
- The captured readiness fetcher blocks IP literals on every manual redirect hop. It does not resolve hostnames. The DNS check in this branch is not in the running version. A later hostname redirect is still unchecked, and DNS can change between the check and the fetch.
- The vote and roast KV counter is one isolate. Optional `ROAST_RL` and `VOTE_RL` bindings are per Cloudflare location once an owner creates them. Neither is a worldwide cap.
- Any slug that matches `^[a-z0-9][a-z0-9-]{0,80}$` can be written into the weekly vote document. The catalog has far more than a few hundred tools, so a small cap would reject real listings. Not changed.
- The MCP worker sets `Access-Control-Allow-Origin: *` and does not set `Access-Control-Allow-Credentials`. Its tools only read the bundled snapshots. Leave the wildcard in place.
- There are no user accounts. Tenant isolation does not apply. The privileged routes above still require the stats key.
