# Needs validation

Twelve leads. None is a confirmed vulnerability. None has a severity. Do not send these inputs to the production hosts.

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

## Roast filter allows transition prefixes that embed a blocked IPv4 address

Fingerprint: `ssrf.isBlockedIp.transition-embed-ipv4`

Claim: `blockedV6` returns false for NAT64 `64:ff9b::/96` and 6to4 `2002::/16`. The host URL parser keeps those hostnames. A full-form IPv4-mapped literal is a different case: it is compressed to `::ffff:` and rejected. `fetchPublic` calls `fetch` when the classifier returns no error.

Trace: `worker.js:249` reads the roast URL, `ssrf.js:87` classifies a colon host, `ssrf.js:57` returns false for these prefixes, `worker.js:205` fetches the URL.

Evidence: `ssrf.js:10` decodes only a leading `::ffff:` string. `ssrf.test.mjs:7` does not include these prefixes.

Blocker: Workers egress translation for these prefixes is not in the repository.

Local check: call `validateUrlShape` on `http://[64:ff9b::a00:1]/` and `http://[2002:a9fe:a9fe::]/` with `fetch` stubbed. Do not contact a deployed host.

Owner check: read the account egress policy on an isolated worker. Do not point production at a link-local address.

Source change that closes the traced gap: decode the embedded IPv4 address for `64:ff9b::/96`, `64:ff9b:1::/48`, and `2002::/16`, and return `blockedV4`.

## One visitor can pass the vote dedup check twice

Fingerprint: `votes.kv-check-then-act`

Claim: the seen flag, the daily salt, and the week document are separate unconditional KV writes. Two overlapping calls can both see an empty seen key. `dailySalt` keeps a private UUID when the follow-up read is empty, so the seen hashes can differ and both calls can increment.

Trace: `worker.js:319` dispatches `POST /vote`, `worker.js:158` mints the salt, `worker.js:280` reads the seen key, `worker.js:286` writes the flag and the document.

Evidence: `worker.js:8` already says overlapping votes can drop a count. `votes.test.mjs:86` covers only an in-order second vote.

Blocker: the overlapping schedules were not executed.

Local check: two `POST /vote` calls for one slug and one address against a KV stub where both seen reads return empty. Record the stored count. Do not send them to a deployed host.

Source change that closes the traced gap: create the seen key only if it is absent, and use only the salt value that was stored for that day.

## Site build can install any later Pillow release

Fingerprint: `requirements.pillow.unbounded-install`

Claim: `requirements.txt` allows any Pillow at or above 13.0.0. The build notes run `pip install -U`. `build_site.py` imports that package through `build_logocheck` before it writes pages.

Trace: `requirements.txt:4`, `cloudflare-image-worker-patches/README.md:97`, `build_logocheck.py:9`.

Blocker: no workflow shows that the live build uses this install rather than a frozen environment.

Local check: install from a fixture index and record the Pillow version. Do not use a public index.

Source change that closes the traced gap: pin an exact Pillow version beside the other exact pins.

## MCP link checker treats shared address space as public

Fingerprint: `check_mcp_links.public.shared-address-space`

Claim: `public()` rejects only the listed `ipaddress` flags. On this host, `100.64.0.1` sets none of them. The roast worker rejects `100.64.0.0/10`. This script then requests a URL `public()` accepted.

Trace: `scripts/check_mcp_links.py:54` queues catalog URLs, line 21 classifies addresses, line 40 requests the URL.

Evidence: `ssrf.js:39` rejects that IPv4 range.

Blocker: whether the operator host routes `100.64.0.0/10` is not in the repository.

Local check: record `is_private` and `is_global` for `100.64.0.1`, then call `public()` with a fixture resolver. Stop at the boolean.

Source change that closes the traced gap: reject an address when `is_global` is false.

## Adding a tool fetches homepage and icon URLs with no address check

Fingerprint: `add_tools.verify.unguarded-fetch`

Claim: `verify()` downloads a GitHub homepage when the website cell is empty, then `getimg()` downloads icon URLs from that page. Neither call classifies the address. Redirects stay enabled.

Trace: `scripts/add_tools.py:84` takes the homepage, line 90 downloads it, line 100 collects icon hrefs, line 42 reads the icon body.

Evidence: `scripts/check_mcp_links.py:13` already has `public()`, and `add_tools.py` does not call it.

Blocker: the fetch was not executed.

Local check: point an icon href at a listener on `127.0.0.1` and record whether it accepts a connection. Do not use a metadata address.

Source change that closes the traced gap: run those URLs through `public()` before `requests.get`.
