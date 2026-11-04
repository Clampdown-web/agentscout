# Needs validation

Seven leads. None is a confirmed vulnerability. None has a severity. Do not send these inputs to the production hosts.

## Roast fetch is not bound to the checked DNS answers

Fingerprint: `ssrf.fetch-unpinned-dns`

Claim: `resolveAndCheck` accepts a public answer, and `fetchPublic` then calls `fetch` on the hostname. `dns.addresses` is not the connection target. Manual redirects call `fetchPublic` again.

Trace: `worker.js:254` `fetchPublic`, `ssrf.js:112` DNS-over-HTTPS, `worker.js:205` `fetch(shape.url)`.

Evidence: `worker.js:199` uses the DNS result as an error check. `worker.js:215` follows `Location` by calling `fetchPublic`.

Blocker: the repository does not show whether the runtime re-resolves the hostname inside one request.

Local check: stub `fetch` so the DNS response is a public address and record the next URL. Assert that URL still contains the hostname.

Owner check: ask whether Workers `fetch` is pinned to an earlier DNS-over-HTTPS answer from the same isolate. Do not run a rebinding test against production.

Source change that closes the traced gap: connect only to an address the check accepted, and fail closed when the peer address is outside that list.

## Roast limiting is per-isolate when vote storage is absent

Fingerprint: `roast.rate-limit-fallback`

Claim: `rateLimit` uses a module `Map` when `env.VOTES` is missing, and `roast` still fetches. The KV path is get-then-put. `POST /vote` returns 503 in that same missing-binding case.

Trace: `worker.js:247` calls `rateLimit`, `worker.js:134` selects the binding, `worker.js:254` continues into `fetchPublic`.

Evidence: `worker.js:140` memory fallback, `worker.js:270` vote fail-closed, `wrangler.toml:24` declares the binding.

Blockers: overlapping KV writes were not run. Whether the deployed worker can start without the binding is not proven by the manifest alone.

Local check: call the limiter with no binding from two copies, and with a KV double that returns the same count to two gets. Do not burst production.

Owner check: confirm the `VOTES` binding is attached. Do not send a burst to production.

Source change that closes the traced gap: return 503 from `roast` when `env.VOTES` is missing.

## Client address falls back to X-Forwarded-For

Fingerprint: `workers.client-ip-forwarded`

Claim: `clientIp` in the votes worker (`worker.js:66`), the MCP worker (`worker.js:151`), and the image patch (`security.js:116`) uses `cf-connecting-ip` and otherwise the first `X-Forwarded-For` value. That value is the vote seen-key input (`worker.js:278`) and the Turnstile `remoteip` (`security.js:187`).

Blocker: source does not show a request reaching these handlers without the platform header.

Local check: call each `clientIp` with only `X-Forwarded-For`, and again with `cf-connecting-ip`. Record which value is used.

Owner check: confirm every production route sets `CF-Connecting-IP` and drops a client-supplied copy before the worker. Do not spoof the header against production.

Source change that closes the traced gap: require `cf-connecting-ip` and fail closed when it is absent.

## Image patch does not origin-check or rate-limit /generate

Fingerprint: `image.generate-ungated`

Claim: `guardedKind` (`security.js:61`) ignores `/generate`, so `gate()` does not apply the origin list or `IMAGE_WRITE`. `rejectTurnstile` (`security.js:171`) returns immediately unless `TURNSTILE_ENABLED` is the string `true`. `security.test.mjs:283` expects a foreign `POST /generate` with an empty env to reach the inner handler. `generate.js:25` posts the prompt to that route. `entry.js:5` shows the inner worker a false flag.

Blockers: the inner handler is not in the repo. The deployed flag is not in the repo. The test was not executed.

Local check: run `node --test cloudflare-image-worker-patches/security.test.mjs` in a network-blocked sandbox. Confirm the foreign `/generate` case and the case where the flag is true and siteverify fails.

Owner check: read the deployed flag and the inner `/generate` quota. Do not send generation requests to production.

Source change that closes the traced gap: apply the submit origin allowlist and `IMAGE_WRITE` to `POST /generate` even when the flag is unset.

## Image entrypoint hides Turnstile from the inner worker

Fingerprint: `image.turnstile-flag-masked`

Claim: `entry.js:7` exports `protect(existing)`. `entry.js:6` calls the inner fetch through `innerEnv`. That proxy returns the string `false` for `TURNSTILE_ENABLED` (`entry.js:5`). The wrapper's own siteverify (`security.js:171`) covers only two POST paths, and only when the real flag is true.

Blocker: `index.js` is imported and is not in the repository, so its Turnstile branches cannot be compared with `TURNSTILE_PATHS`.

Local check: compare those inner branches with `TURNSTILE_PATHS`. A check on any other path sees the flag as off.

Owner check: diff the deployed bundle against `entry.js`. Do not send tokens to production.

Source change that closes the traced gap: remove the `innerEnv` proxy until `index.js` is reviewed beside `protect()`.

## Readiness and share routes are outside the image patch

Fingerprint: `image.passthrough-handlers-absent`

Claim: `readiness.js:25` sends the visitor URL to `/readiness`. `gate` (`security.js:204`) returns immediately when the path is not submit, review, or reviews. `protect` then calls the inner fetch (`security.js:247`). The file comment at `security.js:6` says `/track`, `/readiness`, `/geo`, and `/share` are unchanged. `README.md:3` says the image worker source is not in this repository.

Blocker: the server that fetches `/readiness` is not in the tree, so its allowlist cannot be read.

Local check: place that handler next to `cloudflare-api-worker/src/ssrf.js` and compare the URL checks.

Owner check: identify the deployed script for `/readiness` and record whether it fetches the query URL. Do not send an internal URL to production.

Source change that closes the traced gap: before that fetch, accept the URL only through `validateUrlShape` and `isBlockedIp`.

## Review stars are concatenated into tool-page HTML

Fingerprint: `reviews.stars.html-interpolation`

Lower-trust caller: a visitor whose review is later rendered on a tool page, if the missing review store accepts a non-numeric `stars` value.

Claim: `reviews.js` escapes the reviewer name and the review text, then concatenates `r.stars` into the screen-reader span and assigns the string to `innerHTML`. `stars()` coerces a separate copy for the CSS variable. `build_reviews.py` interpolates the same field without `html.escape`. The form sends a number from the 1 to 5 radios. Tool pages ship `script-src 'unsafe-inline'`.

Trace:

1. `reviews.js:49` loads `GET /reviews?tool=`.
2. `reviews.js:45` concatenates the raw `r.stars` value.
3. `reviews.js:44` assigns that HTML to the review list.

Evidence: `reviews.js:23` (the escaper used for name and text), `reviews.js:31` (numeric coercion for the CSS variable only), `reviews.js:69` (the form sends a number), `build_reviews.py:26` (static HTML uses the same raw field), `cloudflare-image-worker-patches/entry.js:1` (the inner module is not in the repo).

Blocker: the review store and the `GET /reviews` serializer are not in the repository, so a string `stars` value cannot be ruled in or out.

Local check: with the owner-held image-worker `index.js`, record whether `stars` is forced to an integer from 1 to 5 before it is stored and before it is JSON-encoded. Do not submit markup to the deployed API.

Owner check: inspect the deployed review worker, or one existing review record, and record the JSON type of `stars`.

Source change that closes the traced gap: in `reviews.js` and `build_reviews.py`, put the star count through `esc` or the numeric coercion `stars()` already uses before it is placed in HTML.
