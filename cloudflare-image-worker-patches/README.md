# agentscout-image security patch

The worker behind `api.agentscouthq.com` is **agentscout-image**. Its source is not in this repository and not in git history. `/submit`, `/review`, and `/reviews` run there, along with `/generate`, `/track`, `/readiness`, `/geo`, `/share`, and `/stats`.

This folder is a drop-in for that worker. It does not change the Pages site by itself. Deploy it only on **agentscout-image**, after this pull request is merged, and do not deploy it from this repository.

## What the middleware does

Same origin check as `cloudflare-api-worker/src/worker.js` (`allowOrigin` / `voteAllowed`):

- Allowed origins are only `https://agentscouthq.com` and `https://www.agentscouthq.com`.
- Responses on the guarded paths set `Access-Control-Allow-Origin` to that origin and delete any `*` the current worker sends. A foreign `Origin` gets no allow-origin header.
- `POST` is rejected with 403 unless `Origin` is on that list. If `Origin` is absent, `Referer` must be one of those origins. A spoofed `User-Agent` is not a bypass.
- Per-IP limits use the Workers Rate Limiting binding, keyed by `CF-Connecting-IP`:
  - `IMAGE_WRITE`: **10 requests / 60 seconds** for `POST` (and any method that is not `GET` or `HEAD`)
  - `IMAGE_READ`: **120 requests / 60 seconds** for `GET` and `HEAD`
- `OPTIONS` is not counted. A preflight from a foreign origin is 403.
- If either binding is missing, a guarded request returns **503**. It does not fall open.

The review form in `reviews.js` posts to **`/review`**, not `/reviews`. Both are guarded. `GET /reviews` and `GET /reviews/all` (used by tool pages and category sort) are the read path. `/generate`, `/track`, `/readiness`, `/geo`, `/share`, and `/stats` are passed through untouched.

These limits are per Cloudflare location and approximate. They are still shared by every isolate in that location, which is the failure mode of an in-memory `Map`.

`namespace_id` must be unique in the Cloudflare account. `481201` and `481202` are unused by the MCP worker (`481015`, `481060`). If a dashboard check shows either id already taken, pick another positive integer and keep the binding **names** `IMAGE_WRITE` and `IMAGE_READ`.

## Apply it

1. Copy `security.js` into the agentscout-image project, next to its entry file.
2. Wrap the existing export. Do not rewrite the submit or review handlers.

```js
import existing from "./index.js";
import { protect } from "./security.js";

export default protect(existing);
```

If the worker is a single file that already says `export default { async fetch(...) { ... } }`, change that to:

```js
import { protect } from "./security.js";

const existing = {
  async fetch(request, env, ctx) {
    // leave the current fetch body here, unchanged
  },
};

export default protect(existing);
```

3. Add the `ratelimits` array from `wrangler.ratelimits.jsonc` to that worker's Wrangler config (the file you actually deploy). Keep the existing worker name `agentscout-image`. Do not attach this worker config to `votes.agentscouthq.com` or `mcp.agentscouthq.com`.
4. From the image-worker project, deploy **only** that worker:

```sh
npx wrangler deploy
```

5. Check, from outside the site origin:

```sh
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://api.agentscouthq.com/submit \
  -H 'Origin: https://evil.example' -H 'Content-Type: text/plain' --data '{}'
```

That must be `403`. The same POST with `-H 'Origin: https://agentscouthq.com'` must not be `403` from this middleware (the existing handler may still return 400 for an empty body). Eleven rapid POSTs from one IP must include a `429`. `GET /reviews/all` with `-H 'Origin: https://agentscouthq.com'` must answer `access-control-allow-origin: https://agentscouthq.com`. The same GET with a foreign `Origin` must not reflect that origin. `POST /generate` must behave as it does today.

## Test the patch before you copy it

From the agentscout repo root:

```sh
node --test cloudflare-image-worker-patches/security.test.mjs
```
