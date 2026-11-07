# Staged recovery plan

This is a plan and a comparison with the captured image-worker source. It is not a restore. No backup download, PITR restore, or worker deploy was run for this document.

Merging the pull request updates git. It does not publish a Worker and it does not put the new `/reviews/export` route on the running script.

## Captured image worker

Content API capture on 2026-11-07, about 10:19 PT. Script version `1c6368ca-f9d5-403e-92c2-7954641c2153`. Pattern scan of the four modules reported zero common secret-assignment hits. That is not a proof that no secret exists.

| Module | SHA-256 | Bytes |
| --- | --- | --- |
| entry.js | `26986e85df8683c41a204a4afd79a9f2cd9f3a33922091135b8c1460dadf5713` | 571 |
| index.js | `cf43a7a555662357f7aa7cde5474194213d749add2a7e264705f4f907b056f15` | 62355 |
| security.js | `11f6c72232d9a3c422422ed9b3b638c0065bf3cfcba4e8f9035aacb05b4b138c` | 11415 |
| ssrf.js | `dad6679867b0812bd53e3c6a17a27fcbb6b6d7c03726abd851c714abb9de98d6` | 6567 |

Those bytes are not committed here. The checksum-verified Drive archive is the copy of that capture. Live `security.js` matches the pre-PR file except it imports `./ssrf.js` and has no trailing newline. Live `ssrf.js` and `entry.js` match the pre-PR files except the missing newline. The running `ssrf.js` already blocks IPv4-mapped `::ffff:0:0/96`, NAT64, and 6to4. This branch adds the deprecated IPv4-compatible form (the first 96 bits zero, such as `::7f00:1`). The DNS check in the image guard, the stricter limiter result, and the mask inside `protect()` are in this branch and are not in that captured `security.js`.

The capture listed no zone routes. Preview and `workers.dev` URLs are enabled. This plan does not treat a hostname as proven.

`TURNSTILE_ENABLED` is the string `true`. These secret names are present and encrypted: `TURNSTILE_SECRET`, `STATS_KEY`, `REVIEW_HMAC`, `AE_TOKEN`, `INTERNAL_IP_SHA`. `REVIEW_TURNSTILE` exists; its value was not read. Do not print any of those values.

Distinct rate-limit namespaces on that script: `TRACK_RL` 1001 at 20/min, `REVIEW_RL` 1002 at 6/min, `READY_RL` 1003 at 10/min, `IMAGE_WRITE` 481201 at 10/min, `IMAGE_READ` 481202 at 120/min.

## What the inner handler actually does

Compared with the earlier skeptical notes, using the captured `index.js`:

- Duplicate `url` values are not a second fetch. Readiness uses the first `url` only. A parameter named `target` is ignored. The outer gate does the same. This is not a bypass of the fetcher.
- Readiness blocks IP literals, `localhost`, and names ending in `.local`, `.internal`, or `.invalid` before fetch. Redirects are manual, at most four hops, and each hop repeats that name check. A redirect to `127.0.0.1` or `metadata.google.internal` stops. A normal hostname is not DNS-checked by that loop. The captured loop will fetch it. `protect()` in this branch, which is not the running script, checks DNS on every request that uses the readiness User-Agent, including later hops, and does not perform the fetch when the lookup fails or returns a blocked address. The lookup and the fetch are still two steps. The runtime resolves the name again. The address is not pinned, because connecting to the raw address would skip the certificate check for the hostname. A change in that gap is still possible. This is not a proof that every SSRF path is closed.
- `POST /generate` siteverify in the inner handler runs only when it sees `TURNSTILE_ENABLED === "true"`. Live `entry.js` masks that flag on `POST /submit` and `POST /generate` after the outer check. With the flag truly `true`, the token is spent once. `POST /submit` does not siteverify again inside `handleSubmit`.
- `POST /review` is not siteverified by the outer guard. The inner handler siteverifies only when `REVIEW_TURNSTILE` is the string `true` and `TURNSTILE_SECRET` is set. It checks `success` and does not check `hostname`. Because the value of `REVIEW_TURNSTILE` was not read, this plan does not say whether review tokens are required in production. The outer guard does not mask `REVIEW_TURNSTILE`. Adding an outer siteverify without masking that flag would spend the token twice.
- The captured `REVIEW_RL` and `TRACK_RL` calls treat a thrown `limit()` as success. The captured readiness object call does the same with `ok: true`. `READY_RL` has no catch. `protect()` in this branch wraps those four bindings when they exist: a throw or a result other than success or `ok: true` becomes a rejection, and a real success is unchanged. A missing binding is left missing. That does not add a global cap. `POST /review` still has the outer `IMAGE_WRITE` gate. `/track` does not. Do not remove `TRACK_RL`, `REVIEW_RL`, `READY_RL`, `IMAGE_READ`, or `IMAGE_WRITE`. The votes worker's `ROAST_RL` and `VOTE_RL` stay optional and are not created here.
- `/reviews/pending` and `/reviews/admin` compare `X-Stats-Key` with `!==` inside the handler and return 401. The outer guard compares with a hash and returns 403 before the handler. `/review/moderate` is a separate HMAC link, not a stats-key route. The inner router has no `/reviews/admin/extra` style path.
- `ReviewsDO` is one SQLite object named `all`. Tables are `ratings (tool, vid, iph, stars, ts)`, `reviews (id, tool, vid, iph, stars, name, body, status, ts)`, and `limits (k, n, exp)`. `iph` is a hash, not a raw address. `ReadyLimitDO` uses the key-value storage API, not SQL.

## Drive archive, and what it is not

The encrypted Drive archive has been uploaded and its round trip checksum was verified. It contains older `main` `24ac42ab`, the deployed image sources, and a separate DNS/votes supplement. It does not contain the reviews rows, an `agentscout-x-media` script, or secret values. Key-independent storage is still pending. That archive is not a tested full-service restore.

## Stages

Do these only after an explicit approval for that stage. Rolling one stage back does not roll the others back.

1. **Git and Pages.** Revert the merge commit if the static site should go back. Pages may start serving new files under `docs/` and the worker patch directory. Those files do not execute. HTML, `_headers`, and the catalog and SEO builders are unchanged in this branch. Workflow `.github/workflows/security.yml` only checks out, tests, and audits. It cannot deploy.
2. **Image worker code.** The known-good running version is `1c6368ca-f9d5-403e-92c2-7954641c2153`. Dashboard rollback to that version undoes a later deploy of this branch. Deploy this branch only by copying `cloudflare-image-worker-patches/entry.js`, `security.js`, `reviews-backup.js`, and `cloudflare-api-worker/src/ssrf.js` into the project that already has the captured `index.js`, then deploying that project. Do not `wrangler deploy` from the repository root. Copying `security.js` without the updated `ssrf.js` makes public CNAME hosts fail the new readiness check. The captured `ReviewsDO` constructor sets `this.sql` from `ctx.storage.sql`. The subclass calls that handle. `GET /reviews/export` stays a 404, and does not touch the object, unless the plain-text var `REVIEWS_EXPORT` is the string `true`. This repo does not set that var. Turning it on is a separate approval from deploying the other guard changes.
3. **Reviews rows.** SQLite-backed Durable Objects expose point-in-time recovery for 30 days: `getCurrentBookmark`, `getBookmarkForTime`, and `onNextSessionRestoreBookmark`, then a restart. The API is not available in local development. It covers that object's SQL and key-value data. It was not called here. Do not describe a live restore as done. The 30-day window is not a substitute for an off-box copy. With `REVIEWS_EXPORT` set to `true`, `GET /reviews/export` is an admin page of at most 100 rows, stats-key required, `no-store`, no CORS header on the row payload. It returns plaintext JSON so the operator can place it in the encrypted archive. The route is absent from version `1c6368ca-f9d5-403e-92c2-7954641c2153`.
4. **Votes.** Source of a future deploy is `cloudflare-api-worker/`. The KV namespace id is in `wrangler.toml` and is an identifier, not a credential. The per-isolate lock is not a global cap. `ROAST_RL` and `VOTE_RL` are used only when those bindings exist. This branch does not create them. Workers Rate Limiting is shared by isolates in one location. It is still not one worldwide counter. A single Durable Object counter is not part of this change.
5. **MCP.** Source is `cloudflare-mcp-worker/`. This follow-up does not change its runtime. Wildcard CORS stays.
6. **`agentscout-x-media`.** No worker source, Wrangler file, or package by that name is in this repository. Static clips that are in git and can be copied from the tree are `assets/x/` and `assets/animations/`. If a separate media worker exists, its script is missing from this repo and from the Drive archive described above.
7. **Secrets.** They stay in the existing encrypted bindings. This plan does not rotate them and does not store them.
8. **Alerts.** SSL certificate alert policy `b470d63a005a4d548e00f488e1a888e3` exists and notifies AgentScoutHQ@gmail.com. Worker error alerts are not enabled. This branch does not change alert settings and does not claim an off-box restore succeeded.

## Isolated check

From the repo root, with no network and no Cloudflare credentials:

```sh
node --test cloudflare-image-worker-patches/captured-handler.test.mjs cloudflare-image-worker-patches/security.test.mjs cloudflare-image-worker-patches/backup.test.mjs cloudflare-api-worker/test/ssrf.test.mjs cloudflare-api-worker/test/ratelimit.test.mjs
```

That runs the captured readiness loop and the captured limiter catches through `protect()`. It does not restore production.

## Smallest approval package

Before any image deploy, the owner approves that deploy in writing. The package is the four patch files named in stage 2, the tests in this branch, and rollback to version `1c6368ca-f9d5-403e-92c2-7954641c2153`. Leave `REVIEWS_EXPORT` unset on that deploy. The export route needs its own yes, which is setting that var to `true` afterward. A Pages merge is a different yes, and it still does not enable the worker changes.
