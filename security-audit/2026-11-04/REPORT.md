# Security audit report

## Run

| Item | Value |
| --- | --- |
| Profile | standard |
| Scope | whole repository |
| Budget | unset |
| Source | `0668a45610a2bb0d2e0165927d90bb0b36c7d5ce` on `main` (clean worktree) |
| Execution | sandboxed source-and-local only |
| Prior runs | none |

Target code was not executed. `unshare --net` can drop outbound network, and `unshare --mount-proc` fails. bubblewrap, firejail, and nsjail are not installed, so a read-only target mount and a full resource sandbox were not available. Leads that need a function result or a missing file stay `needs_validation`. The live site was not probed.

Delegated hunter and verifier agents had not returned structured JSON when this ledger was closed. The parent re-read every cited file and line against this commit and did not promote any lead to `confirmed`. A separate coverage-critic agent did not return a pass, so this report does not claim a critic-accepted clean sweep. No prior ledger was carried forward.

Counts: **confirmed 0**, **needs_validation 12**, **rejected 5**.

## Security posture

The in-repo workers are a public read-only MCP catalog, a votes and roast worker, and a patch around an image worker whose inner program is not in this tree. Vote and submit routes check the site Origin. The stats-key compare fails closed when the secret is unset. The MCP limiter fails closed when its bindings are missing, and a User-Agent string is not a bypass. The roast fetcher limits scheme, port, body size, and redirect hops, and it rejects the private addresses its tests name. `new URL` serializes a full-form IPv4-mapped literal to the `::ffff:` spelling that `isBlockedIp` already rejects. The fetch that follows a public DNS answer is still not bound to those addresses. Browser sinks reviewed on the shared scripts escape catalog and URL text before `innerHTML`. No hardcoded cloud secret or private key literal was found.

## Confirmed findings

None. No record has a bounded local observation, so none has a severity.

## Needs validation

These are source-traced leads with an exact blocker. They are not confirmed vulnerabilities and they have no severity.

| Lead | Trace | Blocker | Local next step |
| --- | --- | --- | --- |
| Roast fetch is not bound to the checked DNS answers | `fetchPublic` after `resolveAndCheck` | Whether the runtime re-resolves the hostname is outside the repo | Stub `fetch` and record that the second call still uses the hostname |
| Roast limiting is per-isolate when vote storage is absent | `rateLimit` memory fallback | Deployed KV attachment and overlapping KV writes were not run | Scratch harness with no `VOTES` binding and a double get |
| Client address falls back to X-Forwarded-For | `clientIp` in three workers | Whether a request can arrive without `CF-Connecting-IP` is not in the repo | Call `clientIp` on two local `Request` objects |
| Image patch does not origin-check or rate-limit `/generate` | `guardedKind` and `security.test.mjs` | Inner `/generate` handler and the deployed flag are absent | Run the patch test in a network-blocked sandbox |
| Image entrypoint hides Turnstile from the inner worker | `entry.js` `innerEnv` | `index.js` is not in the repo | Diff the inner Turnstile branches against `TURNSTILE_PATHS` |
| Readiness and share routes are outside the image patch | `readiness.js` to `protect` | The server handler is not in the repo | Read the inner `/readiness` fetcher next to `ssrf.js` |
| Review stars are concatenated into tool-page HTML | `reviews.js` review list | The review store is not in the repo | Read the owner-held `POST /review` serializer and record the JSON type of `stars` |
| Roast filter allows NAT64 and 6to4 prefixes that embed a blocked IPv4 address | `ssrf.js` `blockedV6` | Workers egress translation is not in the repo | Call `validateUrlShape` on those literals with `fetch` stubbed |
| One visitor can pass the vote dedup check twice | `worker.js` `dailySalt` and the seen-key puts | KV interleaving was not executed | Two overlapping `POST /vote` calls against a KV stub |
| Site build can install any later Pillow release | `requirements.txt` `pillow>=13.0.0` | The wheel a build machine installs was not observed | Install from a fixture index and record the version |
| MCP link checker treats 100.64.0.0/10 as public | `scripts/check_mcp_links.py` `public` | Operator routing for that range is not in the repo | Record `is_private` and `is_global` for `100.64.0.1`, then call `public()` on a fixture |
| Adding a tool fetches homepage and icon URLs with no address check | `scripts/add_tools.py` `verify` and `getimg` | The fetch was not executed | Point an icon href at a local listener and record the connection |

The source change that closes each traced gap, once the local check agrees:

- **Unpinned DNS.** Make `fetchPublic` connect to an address `resolveAndCheck` accepted, or fail closed when the runtime peer address is not in that list.
- **Roast limiter.** Return 503 from `roast` when `env.VOTES` is missing, matching `POST /vote`.
- **Forwarded client IP.** Read only `cf-connecting-ip` and fail closed when it is absent. Use that value for vote dedup, rate limits, and Turnstile `remoteip`.
- **`/generate`.** Put `POST /generate` through the same origin allowlist and `IMAGE_WRITE` limit as `POST /submit`, including when `TURNSTILE_ENABLED` is unset.
- **Masked Turnstile flag.** Remove the `innerEnv` proxy until `index.js` is in the tree and its checks are compared with `protect()`.
- **Passthrough routes.** Run `/readiness` through `validateUrlShape` and `isBlockedIp` before any server fetch. The handler has to be reviewed first.
- **Review stars.** In `reviews.js` and `build_reviews.py`, put the star count through `esc` or the same numeric coercion `stars()` already uses before it is placed in HTML.
- **Transition prefixes.** In `blockedV6`, decode the embedded IPv4 address for `64:ff9b::/96`, `64:ff9b:1::/48`, and `2002::/16`, and return `blockedV4` for that address.
- **Vote dedup.** Write the seen key with a create-if-absent operation, and use only the salt value stored for that day.
- **Pillow.** Pin an exact Pillow version next to the other exact pins in `requirements.txt`.
- **Shared address space.** Reject an address in `public()` when `is_global` is false, including `100.64.0.0/10`.
- **Tool ingest.** Run homepage and icon URLs through that same `public()` check before `requests.get`.

Owner-observed checks are in `NEEDS-VALIDATION.md`. They do not ask anyone to send these inputs to production.

## Hardening and positive patterns

Hardening, not findings:

- `_headers` CSP is report-only. Pages carry their own enforcing meta CSP.
- `_faq_html` inserts operator-authored answer HTML. A later untrusted answer would need `html.escape`.
- `readiness.js` `row()` does not escape its note argument. Current callers escape dynamic pieces first.
- Vote counts use a KV read-modify-write. The file already says concurrent votes can drop a count. The state is the public tally.
- `safeEq` treats two empty strings as equal. An unset `STATS_KEY` still fails closed.
- MCP CORS is `*`. The handler sets no credentials and serves the public snapshot.
- `check_mcp_links.py` resolves a host and then opens the URL separately.
- Python dependencies in `requirements.txt` are pinned and are not hash-locked. No GitHub Actions workflow is in the repo.
- Two MCP wrangler files use different worker names.

Positive patterns: origin allowlists on vote and guarded submit routes, constant-time compare of hashed stats keys, MCP and image rate-limit bindings that fail closed, roast body and redirect caps, and escaping on the shared card, quiz, review, and roast renderers.

## Coverage

| Status | Units |
| --- | --- |
| covered | 13 |
| candidate | 13 |
| blocked | 0 |
| deferred | 1 |
| out of scope | 0 |

27 units. Twelve fingerprints are linked from the thirteen candidate units (`workers.client-ip-forwarded` is one cause on three workers). Duplicate hunter fingerprints for that same client-address fallback, for `/generate`, for the Turnstile proxy, and for `/readiness` were not filed again. The inner image worker, the advertised MCP SSE handler (`cloudflare-mcp-worker/worker.js` `registryBody`), and the deployed Turnstile flag are absent from source. The SSE handler is the deferred unit. The other absences are the blockers above. Rejected claims, kept so a later run can see the refutation: `build.faq-unescaped-answer`, `crypto.safeeq-empty-equals-empty`, `mcp.wildcard-cors`, `ssrf.ipv6-mapped-private`, `vote.origin-header-as-auth`.
