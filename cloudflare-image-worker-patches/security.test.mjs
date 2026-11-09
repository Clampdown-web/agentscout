import test from "node:test";
import assert from "node:assert/strict";
import { allowOrigin, postAllowed, guardedKind, maskTurnstileEnv, protect, safeEq, statsKeyPath, submitActionDecision, submitActionRequired, turnstileEnabled } from "./security.js";

test("cors allowlist is the site and www only", () => {
  assert.equal(allowOrigin("https://agentscouthq.com"), "https://agentscouthq.com");
  assert.equal(allowOrigin("https://www.agentscouthq.com"), "https://www.agentscouthq.com");
  assert.equal(allowOrigin("https://evil.example"), "");
  assert.equal(allowOrigin("https://agentscouthq.com.evil"), "");
  assert.equal(allowOrigin("https://agentscouthq.com.evil.example"), "");
  assert.equal(allowOrigin(""), "");
});

test("guarded paths are submit, review, and reviews", () => {
  assert.equal(guardedKind("/submit"), "submit");
  assert.equal(guardedKind("/submit/"), "submit");
  assert.equal(guardedKind("/review"), "reviews");
  assert.equal(guardedKind("/reviews"), "reviews");
  assert.equal(guardedKind("/reviews/all"), "reviews");
  assert.equal(guardedKind("/generate"), "generate");
  assert.equal(guardedKind("/readiness"), "");
  assert.equal(guardedKind("/track"), "");
});

function limiter(max) {
  const counts = new Map();
  return {
    async limit({ key }) {
      const n = (counts.get(key) || 0) + 1;
      counts.set(key, n);
      return { success: n <= max };
    },
  };
}

function env() {
  return { IMAGE_WRITE: limiter(10), IMAGE_READ: limiter(120) };
}

function handler(status = 200, extraHeaders = {}) {
  const calls = [];
  const worker = {
    async fetch(request) {
      calls.push(new URL(request.url).pathname);
      return new Response(JSON.stringify({ ok: true }), {
        status,
        headers: { "content-type": "application/json", "access-control-allow-origin": "*", ...extraHeaders },
      });
    },
  };
  return { worker: protect(worker), calls };
}

function post(path, headers = {}, body = "{}") {
  return new Request("https://api.agentscouthq.com" + path, {
    method: "POST",
    headers: { "content-type": "text/plain", "cf-connecting-ip": "203.0.113.10", ...headers },
    body,
  });
}

function turnstileEnv(extra = {}) {
  return { ...env(), TURNSTILE_ENABLED: "true", TURNSTILE_SECRET: "turnstile-secret", ...extra };
}

async function withSiteverify(impl, fn) {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, opts = {}) => {
    const body = opts.body;
    const params = body && typeof body.get === "function" ? body : new URLSearchParams(String(body || ""));
    calls.push({ url: String(url), params });
    return impl(params, calls);
  };
  try {
    await fn(calls);
  } finally {
    globalThis.fetch = original;
  }
}

test("a foreign origin cannot POST /submit or /review", async () => {
  const { worker, calls } = handler();
  const submit = await worker.fetch(post("/submit", { origin: "https://evil.example" }), env());
  assert.equal(submit.status, 403);
  assert.equal(calls.length, 0);
  assert.equal(submit.headers.get("access-control-allow-origin"), null);
  const review = await worker.fetch(post("/review", { origin: "https://agentscouthq.com.evil" }), env());
  assert.equal(review.status, 403);
  assert.equal(calls.length, 0);
});

test("the site origin can POST, and a reflected star is removed", async () => {
  const { worker, calls } = handler();
  const res = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }), env());
  assert.equal(res.status, 200);
  assert.deepEqual(calls, ["/submit"]);
  assert.equal(res.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  const body = await res.json();
  assert.equal(body.ok, true);
});

test("POST with no Origin uses Referer, and a bare POST is rejected", async () => {
  const { worker, calls } = handler();
  const ok = await worker.fetch(post("/reviews", { referer: "https://www.agentscouthq.com/tools/cursor.html" }), env());
  assert.equal(ok.status, 200);
  const bare = await worker.fetch(post("/submit"), env());
  assert.equal(bare.status, 403);
  assert.equal(postAllowed(post("/submit", { "user-agent": "Googlebot" })), false);
  assert.equal(calls.length, 1);
});

test("GET /reviews/all keeps the site origin and does not reflect a foreign one", async () => {
  const { worker } = handler();
  const headers = { "cf-connecting-ip": "203.0.113.10", "x-agentscout-app": "1" };
  const site = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/all", {
    headers: { ...headers, origin: "https://agentscouthq.com" },
  }), env());
  assert.equal(site.status, 200);
  assert.equal(site.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  const foreign = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/all", {
    headers: { ...headers, origin: "https://evil.example" },
  }), env());
  assert.equal(foreign.status, 200);
  assert.equal(foreign.headers.get("access-control-allow-origin"), null);
});

test("an allowed preflight lists the review header, a foreign preflight is 403", async () => {
  const { worker, calls } = handler();
  const ok = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/all", {
    method: "OPTIONS",
    headers: { origin: "https://www.agentscouthq.com", "access-control-request-headers": "x-agentscout-app" },
  }), env());
  assert.equal(ok.status, 204);
  assert.match(ok.headers.get("access-control-allow-headers"), /x-agentscout-app/);
  const no = await worker.fetch(new Request("https://api.agentscouthq.com/submit", {
    method: "OPTIONS",
    headers: { origin: "https://evil.example" },
  }), env());
  assert.equal(no.status, 403);
  assert.equal(calls.length, 0);
});

test("the write limit is per IP and a Googlebot user-agent does not skip it", async () => {
  const { worker } = handler();
  const binding = env();
  let last = 200;
  for (let i = 0; i < 11; i++) {
    const res = await worker.fetch(post("/submit", {
      origin: "https://agentscouthq.com",
      "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    }), binding);
    last = res.status;
  }
  assert.equal(last, 429);
  const other = await worker.fetch(post("/submit", {
    origin: "https://agentscouthq.com",
    "cf-connecting-ip": "203.0.113.99",
  }), binding);
  assert.equal(other.status, 200);
});

test("a missing rate limit binding fails closed", async () => {
  const { worker, calls } = handler();
  const res = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }), {});
  assert.equal(res.status, 503);
  assert.equal(calls.length, 0);
});

test("safeEq matches the whole secret and ignores non-strings", async () => {
  assert.equal(await safeEq("stats-key", "stats-key"), true);
  assert.equal(await safeEq("stats-key", "stats-key-extra"), false);
  assert.equal(await safeEq("stats-key", "stats-kez"), false);
  assert.equal(await safeEq("stats-key", "stats-ke"), false);
  assert.equal(await safeEq("", ""), false);
  assert.equal(await safeEq("", "stats-key"), false);
  assert.equal(await safeEq("stats-key", ""), false);
  assert.equal(await safeEq(null, "stats-key"), false);
  assert.equal(await safeEq("stats-key", undefined), false);
});

test("safeEq hashes to 32 bytes and uses timingSafeEqual when it exists", async () => {
  const seen = [];
  const prior = crypto.subtle.timingSafeEqual;
  crypto.subtle.timingSafeEqual = (left, right) => {
    seen.push(left.length, right.length);
    let diff = 0;
    for (let i = 0; i < left.length; i++) diff |= left[i] ^ right[i];
    return diff === 0;
  };
  try {
    assert.equal(await safeEq("correct-key", "correct-key"), true);
    assert.equal(await safeEq("correct-key", "wrong"), false);
    assert.deepEqual(seen, [32, 32, 32, 32]);
  } finally {
    if (prior) crypto.subtle.timingSafeEqual = prior;
    else delete crypto.subtle.timingSafeEqual;
  }
});

test("admin paths reject a wrong X-Stats-Key before the inner handler", async () => {
  const { worker, calls } = handler();
  const binding = { ...env(), STATS_KEY: "correct-key" };
  for (const path of ["/reviews/pending", "/reviews/admin", "/stats", "/trending/stats"]) {
    assert.equal(statsKeyPath(path), true);
    const denied = await worker.fetch(new Request("https://api.agentscouthq.com" + path, {
      headers: { "X-Stats-Key": "wrong-key", "cf-connecting-ip": "203.0.113.10", origin: "https://agentscouthq.com" },
    }), binding);
    assert.equal(denied.status, 403);
    const allowed = await worker.fetch(new Request("https://api.agentscouthq.com" + path + "?days=7", {
      headers: { "x-stats-key": "correct-key", "cf-connecting-ip": "203.0.113.10", origin: "https://agentscouthq.com" },
    }), binding);
    assert.equal(allowed.status, 200);
  }
  assert.deepEqual(calls, ["/reviews/pending", "/reviews/admin", "/stats", "/trending/stats"]);
  const missing = await worker.fetch(new Request("https://api.agentscouthq.com/stats"), binding);
  assert.equal(missing.status, 403);
  assert.equal(calls.length, 4);
});

test("stats routes consume the read limit before the key is compared", async () => {
  const { worker, calls } = handler();
  const tight = limiter(2);
  const binding = { ...env(), IMAGE_READ: tight, STATS_KEY: "correct-key" };
  const headers = { "cf-connecting-ip": "203.0.113.77", "x-stats-key": "guess" };
  assert.equal((await worker.fetch(new Request("https://api.agentscouthq.com/stats", { headers }), binding)).status, 403);
  assert.equal((await worker.fetch(new Request("https://api.agentscouthq.com/stats", { headers }), binding)).status, 403);
  const limited = await worker.fetch(new Request("https://api.agentscouthq.com/trending/stats", { headers }), binding);
  assert.equal(limited.status, 429);
  assert.equal(calls.length, 0);
  const ok = await worker.fetch(new Request("https://api.agentscouthq.com/stats", {
    headers: { "cf-connecting-ip": "203.0.113.78", "x-stats-key": "correct-key" },
  }), { ...env(), STATS_KEY: "correct-key" });
  assert.equal(ok.status, 200);
  const unconfigured = await worker.fetch(new Request("https://api.agentscouthq.com/stats", {
    headers: { "cf-connecting-ip": "203.0.113.79", "x-stats-key": "correct-key" },
  }), { STATS_KEY: "correct-key" });
  assert.equal(unconfigured.status, 503);
  assert.equal(calls.length, 1);
});

test("turnstile stays off until TURNSTILE_ENABLED is true", async () => {
  assert.equal(turnstileEnabled({}), false);
  assert.equal(turnstileEnabled({ TURNSTILE_ENABLED: "false" }), false);
  assert.equal(turnstileEnabled({ TURNSTILE_ENABLED: "true" }), true);
  const { worker, calls } = handler();
  let fetched = false;
  const original = globalThis.fetch;
  globalThis.fetch = async () => { fetched = true; throw new Error("siteverify should not run"); };
  try {
    const res = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }), env());
    assert.equal(res.status, 200);
    assert.deepEqual(calls, ["/generate"]);
    assert.equal(fetched, false);
  } finally {
    globalThis.fetch = original;
  }
});

test("submit and generate require a siteverify pass for this site before other work", async () => {
  await withSiteverify((params) => {
    const token = params.get("response");
    if (token === "good") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "submit" }));
    if (token === "www") return new Response(JSON.stringify({ success: true, hostname: "www.agentscouthq.com" }));
    if (token === "wrong-host") return new Response(JSON.stringify({ success: true, hostname: "evil.example", action: "submit" }));
    if (token === "wrong-action") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "generate" }));
    if (token === "spent") return new Response(JSON.stringify({ success: false, hostname: "agentscouthq.com", "error-codes": ["timeout-or-duplicate"] }));
    if (token === "secret") return new Response(JSON.stringify({ success: false, "error-codes": ["invalid-input-secret"] }));
    return new Response(JSON.stringify({ success: false, hostname: "agentscouthq.com", "error-codes": ["invalid-input-response"] }));
  }, async (calls) => {
    let seen = "";
    const inner = [];
    const worker = protect({
      async fetch(request) {
        inner.push(new URL(request.url).pathname);
        seen = await request.text();
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "content-type": "application/json", "access-control-allow-origin": "*" },
        });
      },
    });
    const binding = turnstileEnv();
    const missing = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ name: "x" })), binding);
    assert.equal(missing.status, 403);
    assert.equal(inner.length, 0);
    const failed = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }, JSON.stringify({ prompt: "cat", turnstileToken: "nope" })), binding);
    assert.equal(failed.status, 403);
    const wrongHost = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "wrong-host" })), binding);
    assert.equal(wrongHost.status, 403);
    const noSecret = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "good" })), turnstileEnv({ TURNSTILE_SECRET: "" }));
    assert.equal(noSecret.status, 403);
    assert.equal(inner.length, 0);
    const ok = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ name: "Widget", turnstileToken: "good" })), binding);
    assert.equal(ok.status, 200);
    assert.equal(JSON.parse(seen).turnstileToken, "good");
    const generated = await worker.fetch(post("/generate", { origin: "https://www.agentscouthq.com", "x-forwarded-for": "198.51.100.9" }, JSON.stringify({ prompt: "cat", turnstileToken: "www" })), binding);
    assert.equal(generated.status, 200);
    assert.equal(generated.headers.get("access-control-allow-origin"), "https://www.agentscouthq.com");
    assert.deepEqual(inner, ["/submit", "/generate"]);
    const verify = calls.filter((call) => call.url.includes("siteverify"));
    assert.equal(verify.length, 4);
    assert.equal(verify[0].params.get("remoteip"), "203.0.113.10");
    assert.equal(verify[0].params.get("secret"), "turnstile-secret");
    assert.equal(verify[0].params.get("response"), "nope");
  });
});

test("POST /generate is origin checked and write limited when turnstile is off", async () => {
  const { worker, calls } = handler();
  const foreign = await worker.fetch(post("/generate", { origin: "https://evil.example" }), env());
  assert.equal(foreign.status, 403);
  assert.equal(calls.length, 0);
  const missing = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }), {});
  assert.equal(missing.status, 503);
  const forwarded = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com", "cf-connecting-ip": "", "x-forwarded-for": "198.51.100.9" }), env());
  assert.equal(forwarded.status, 403);
  const ok = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }), env());
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  assert.deepEqual(calls, ["/generate"]);
  const read = await worker.fetch(new Request("https://api.agentscouthq.com/generate"), {});
  assert.equal(read.status, 200);
});

test("readiness rejects a blocked url before the inner handler", async () => {
  const { worker, calls } = handler();
  const original = globalThis.fetch;
  const lookups = [];
  globalThis.fetch = async (url) => {
    const name = new URL(String(url)).searchParams.get("name");
    lookups.push(name);
    if (name === "rebind.example") {
      return new Response(JSON.stringify({ Answer: [{ type: 5, data: "rebind.example." }, { type: 1, data: "10.0.0.1" }] }), { status: 200 });
    }
    if (name === "cdn.example") {
      return new Response(JSON.stringify({ Answer: [{ type: 5, data: "cdn.example.net." }, { type: 1, data: "1.1.1.1" }] }), { status: 200 });
    }
    if (name === "down.example") return new Response("no", { status: 503 });
    throw new Error("unexpected lookup");
  };
  try {
    const blocked = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("http://[64:ff9b::a00:1]/")));
    assert.equal(blocked.status, 400);
    const mapped = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("http://[0:0:0:0:0:ffff:a9fe:a9fe]/")));
    assert.equal(mapped.status, 400);
    const compatible = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("http://[::7f00:1]/")));
    assert.equal(compatible.status, 400);
    assert.equal(lookups.length, 0);
    const privateName = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://rebind.example/path")));
    assert.equal(privateName.status, 400);
    const down = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://down.example/")));
    assert.equal(down.status, 400);
    const literal = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://1.1.1.1/")));
    assert.equal(literal.status, 200);
    const beforeName = lookups.length;
    const ok = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://cdn.example/")));
    assert.equal(ok.status, 200);
    assert.ok(lookups.length > beforeName);
    assert.equal(lookups.includes("1.1.1.1"), false);
    assert.deepEqual(calls, ["/readiness", "/readiness"]);
  } finally {
    globalThis.fetch = original;
  }
});

test("a missing STATS_KEY binding fails closed", async () => {
  const { worker, calls } = handler();
  for (const path of ["/stats", "/reviews/pending", "/reviews/admin", "/trending/stats"]) {
    const res = await worker.fetch(new Request("https://api.agentscouthq.com" + path, {
      headers: { "X-Stats-Key": "present", "cf-connecting-ip": "203.0.113.10", origin: "https://agentscouthq.com" },
    }), env());
    assert.equal(res.status, 403, path);
  }
  assert.equal(calls.length, 0);
});

test("a rate limiter that does not report success fails closed", async () => {
  const { worker, calls } = handler();
  const binding = env();
  binding.IMAGE_WRITE = { async limit() { return {}; } };
  const empty = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }), binding);
  assert.equal(empty.status, 429);
  binding.IMAGE_WRITE = { async limit() { throw new Error("limiter down"); } };
  const thrown = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }), binding);
  assert.equal(thrown.status, 503);
  assert.equal(calls.length, 0);
});

test("turnstile siteverify failures fail closed before the inner handler", async () => {
  const { worker, calls } = handler();
  const original = globalThis.fetch;
  const body = JSON.stringify({ turnstileToken: "good" });
  try {
    globalThis.fetch = async () => { throw new Error("network"); };
    const offline = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, body), turnstileEnv());
    assert.equal(offline.status, 403);
    globalThis.fetch = async () => new Response("nope", { status: 502 });
    const http = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }, body), turnstileEnv());
    assert.equal(http.status, 403);
    let called = false;
    globalThis.fetch = async () => { called = true; return new Response("{}"); };
    const huge = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "x".repeat(2049) })), turnstileEnv());
    assert.equal(huge.status, 403);
    assert.equal(called, false);
    const noIp = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com", "cf-connecting-ip": "", "x-forwarded-for": "198.51.100.9" }, body), turnstileEnv());
    assert.equal(noIp.status, 403);
    assert.equal(called, false);
    assert.equal(calls.length, 0);
  } finally {
    globalThis.fetch = original;
  }
});

test("submit action transition accepts an empty action and rejects a different one", async () => {
  assert.equal(submitActionRequired({}), false);
  assert.equal(submitActionRequired({ TURNSTILE_REQUIRE_SUBMIT_ACTION: "false" }), false);
  assert.equal(submitActionRequired({ TURNSTILE_REQUIRE_SUBMIT_ACTION: "true" }), true);
  assert.equal(submitActionDecision(undefined, false), "ok");
  assert.equal(submitActionDecision("", false), "ok");
  assert.equal(submitActionDecision("submit", false), "ok");
  assert.equal(submitActionDecision("generate", false), "mismatch");
  assert.equal(submitActionDecision("review", false), "mismatch");
  assert.equal(submitActionDecision(undefined, true), "missing");
  assert.equal(submitActionDecision("", true), "missing");
  assert.equal(submitActionDecision("submit", true), "ok");
  assert.equal(submitActionDecision("generate", true), "mismatch");

  await withSiteverify((params) => {
    const token = params.get("response");
    if (token === "good") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "submit" }));
    if (token === "plain") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com" }));
    if (token === "blank") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "" }));
    if (token === "generate") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "generate" }));
    if (token === "review") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "review" }));
    if (token === "spent") return new Response(JSON.stringify({ success: false, "error-codes": ["timeout-or-duplicate"] }));
    if (token === "malformed") return new Response(JSON.stringify({ success: false, "error-codes": ["invalid-input-response"] }));
    if (token === "secret") return new Response(JSON.stringify({ success: false, "error-codes": ["invalid-input-secret"] }));
    return new Response(JSON.stringify({ success: false }));
  }, async () => {
    const seen = [];
    const worker = protect({
      async fetch(request) {
        seen.push(new URL(request.url).pathname);
        return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } });
      },
    });
    const open = turnstileEnv();
    const strict = turnstileEnv({ TURNSTILE_REQUIRE_SUBMIT_ACTION: "true" });
    const missing = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "plain" })), open);
    assert.equal(missing.status, 200);
    const blank = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "blank" })), open);
    assert.equal(blank.status, 200);
    const generateAction = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "generate" })), open);
    assert.equal(generateAction.status, 403);
    assert.match((await generateAction.json()).error, /Reload it/);
    const reviewAction = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "review" })), open);
    assert.equal(reviewAction.status, 403);
    const strictMissing = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "plain" })), strict);
    assert.equal(strictMissing.status, 403);
    assert.match((await strictMissing.json()).error, /Reload it/);
    const strictBlank = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "blank" })), strict);
    assert.equal(strictBlank.status, 403);
    const strictOther = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "generate" })), strict);
    assert.equal(strictOther.status, 403);
    const strictOk = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "good" })), strict);
    assert.equal(strictOk.status, 200);
    const spent = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "spent" })), open);
    assert.equal(spent.status, 403);
    assert.equal((await spent.json()).error, "The check expired or was already used. Complete it again, then submit.");
    const malformed = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "malformed" })), open);
    assert.equal(malformed.status, 403);
    assert.match((await malformed.json()).error, /Complete it again/);
    const secret = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "secret" })), open);
    assert.equal(secret.status, 403);
    assert.equal((await secret.json()).error, "Bot check failed.");
    const generated = await worker.fetch(post("/generate", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "plain" })), open);
    assert.equal(generated.status, 200);
    const ok = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "good" })), open);
    assert.equal(ok.status, 200);
    assert.deepEqual(seen, ["/submit", "/submit", "/submit", "/generate", "/submit"]);
  });
});

test("protect masks TURNSTILE_ENABLED only after it has checked submit and generate", async () => {
  await withSiteverify(() => new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com", action: "submit" })), async () => {
    const seen = [];
    const worker = protect({
      async fetch(request, binding) {
        seen.push({ path: new URL(request.url).pathname, flag: binding.TURNSTILE_ENABLED, secret: binding.TURNSTILE_SECRET });
        return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
      },
    });
    const binding = turnstileEnv();
    const submit = await worker.fetch(post("/submit", { origin: "https://agentscouthq.com" }, JSON.stringify({ turnstileToken: "good" })), binding);
    assert.equal(submit.status, 200);
    const review = await worker.fetch(post("/review", { origin: "https://agentscouthq.com" }, "{}"), binding);
    assert.equal(review.status, 200);
    assert.deepEqual(seen, [
      { path: "/submit", flag: "false", secret: "turnstile-secret" },
      { path: "/review", flag: "true", secret: "turnstile-secret" },
    ]);
  });
});

test("readiness DNS checks the first url only", async () => {
  const calls = [];
  const worker = protect({
    async fetch(request) {
      calls.push(new URL(request.url).search);
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
    },
  });
  const original = globalThis.fetch;
  globalThis.fetch = async (input) => {
    const name = new URL(String(input)).searchParams.get("name");
    if (name === "ok.example") return new Response(JSON.stringify({ Answer: [{ type: 1, data: "1.1.1.1" }] }), { status: 200 });
    throw new Error("unexpected lookup");
  };
  try {
    const dup = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://ok.example/") + "&url=" + encodeURIComponent("http://127.0.0.1/")));
    assert.equal(dup.status, 200);
    const named = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?target=" + encodeURIComponent("http://127.0.0.1/")));
    assert.equal(named.status, 200);
    assert.equal(calls.length, 2);
  } finally {
    globalThis.fetch = original;
  }
});

test("reviews export requires the stats key and does not add CORS or a cache", async () => {
  const calls = [];
  const reviews = {
    idFromName(name) { calls.push(name); return "id-all"; },
    get() {
      return {
        async backupPage(spec) {
          calls.push(spec.table);
          return { table: spec.table, rows: [{ id: "018f2b3c-7c3a-7c3a-8c3a-7c3a7c3a7c3a" }], next: null, secret: "nope" };
        },
      };
    },
  };
  const worker = protect({
    async fetch() {
      calls.push("inner");
      return new Response("{}", { status: 200 });
    },
  });
  const binding = { ...env(), STATS_KEY: "correct-key", REVIEWS_EXPORT: "true", REVIEWS: reviews };
  const headers = { "cf-connecting-ip": "203.0.113.10", origin: "https://evil.example" };
  const off = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/export?table=reviews", {
    headers: { ...headers, "x-stats-key": "correct-key" },
  }), { ...binding, REVIEWS_EXPORT: "" });
  assert.equal(off.status, 404);
  assert.equal(off.headers.get("access-control-allow-origin"), null);
  assert.equal(calls.length, 0);
  const denied = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/export?table=reviews", { headers }), binding);
  assert.equal(denied.status, 403);
  assert.equal(calls.length, 0);
  const missingBinding = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/export?table=reviews", {
    headers: { ...headers, "x-stats-key": "correct-key" },
  }), { STATS_KEY: "correct-key", REVIEWS_EXPORT: "true", REVIEWS: reviews });
  assert.equal(missingBinding.status, 503);
  assert.equal(calls.length, 0);
  const ok = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/export?table=reviews", {
    headers: { ...headers, "x-stats-key": "correct-key" },
  }), binding);
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get("access-control-allow-origin"), null);
  assert.match(ok.headers.get("cache-control"), /no-store/);
  const body = await ok.json();
  assert.equal(body.secret, undefined);
  assert.equal(JSON.stringify(body).includes("TURNSTILE"), false);
  assert.equal(JSON.stringify(body).includes("REVIEW_HMAC"), false);
  assert.deepEqual(calls, ["all", "reviews"]);
  assert.equal(calls.includes("inner"), false);
  const snapshot = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/snapshot", {
    headers: { ...headers, "x-stats-key": "correct-key" },
  }), { ...binding, REVIEWS_SNAPSHOT: "true" });
  assert.equal(snapshot.status, 200);
  assert.equal(calls.includes("snapshot"), false);
  assert.equal(calls.includes("inner"), true);
});

test("public image routes keep status, JSON shape, and CORS without calling siteverify", async () => {
  const seen = [];
  const worker = protect({
    async fetch(request) {
      const url = new URL(request.url);
      seen.push(request.method + " " + url.pathname);
      return new Response(JSON.stringify({ ok: true, path: url.pathname, query: url.searchParams.get("url") || url.searchParams.get("tool") || "" }), {
        status: 200,
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" },
      });
    },
  });
  const binding = env();
  const ip = { "cf-connecting-ip": "203.0.113.50" };
  const site = { ...ip, origin: "https://agentscouthq.com" };

  const preflight = await worker.fetch(new Request("https://api.agentscouthq.com/reviews", {
    method: "OPTIONS",
    headers: { origin: "https://www.agentscouthq.com", "access-control-request-headers": "content-type, x-agentscout-app" },
  }), binding);
  assert.equal(preflight.status, 204);
  assert.equal(preflight.headers.get("access-control-allow-origin"), "https://www.agentscouthq.com");
  assert.match(preflight.headers.get("access-control-allow-headers"), /content-type/);
  assert.match(preflight.headers.get("access-control-allow-headers"), /x-agentscout-app/);
  assert.equal(preflight.headers.get("access-control-allow-credentials"), null);

  const review = await worker.fetch(new Request("https://api.agentscouthq.com/review", {
    method: "POST",
    headers: { ...site, "content-type": "application/json" },
    body: JSON.stringify({ tool: "cursor", stars: 5, text: "Works well for agents.", name: "Ada", vid: "ab".repeat(16) }),
  }), binding);
  assert.equal(review.status, 200);
  assert.equal(review.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  assert.deepEqual(await review.json(), { ok: true, path: "/review", query: "" });

  const reviews = await worker.fetch(new Request("https://api.agentscouthq.com/reviews?tool=cursor", { headers: site }), binding);
  assert.equal(reviews.status, 200);
  assert.equal(reviews.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  assert.equal((await reviews.json()).query, "cursor");

  const all = await worker.fetch(new Request("https://api.agentscouthq.com/reviews/all", { headers: site }), binding);
  assert.equal(all.status, 200);
  assert.equal((await all.json()).path, "/reviews/all");

  const submit = await worker.fetch(new Request("https://api.agentscouthq.com/submit", {
    method: "POST",
    headers: { ...site, "content-type": "text/plain;charset=UTF-8" },
    body: JSON.stringify({ name: "Widget", url: "https://example.com" }),
  }), binding);
  assert.equal(submit.status, 200);
  assert.equal(submit.headers.get("access-control-allow-origin"), "https://agentscouthq.com");

  const generate = await worker.fetch(new Request("https://api.agentscouthq.com/generate", {
    method: "POST",
    headers: { ...site, "content-type": "text/plain;charset=UTF-8" },
    body: JSON.stringify({ prompt: "A friendly robot", turnstileToken: "" }),
  }), binding);
  assert.equal(generate.status, 200);
  assert.equal((await generate.json()).path, "/generate");

  const generateGet = await worker.fetch(new Request("https://api.agentscouthq.com/generate", { headers: ip }), {});
  assert.equal(generateGet.status, 200);
  assert.equal(generateGet.headers.get("access-control-allow-origin"), "*");

  for (const path of ["/track", "/geo", "/share"]) {
    const res = await worker.fetch(new Request("https://api.agentscouthq.com" + path, { headers: ip }), {});
    assert.equal(res.status, 200, path);
    assert.equal((await res.json()).path, path);
  }
  const sharePost = await worker.fetch(new Request("https://api.agentscouthq.com/share", {
    method: "POST",
    headers: { ...site, "content-type": "text/plain" },
    body: JSON.stringify({ path: "/tools/cursor.html" }),
  }), {});
  assert.equal(sharePost.status, 200);
  assert.equal((await sharePost.json()).path, "/share");

  const original = globalThis.fetch;
  globalThis.fetch = async (input) => {
    const name = new URL(String(input)).searchParams.get("name");
    if (name === "example.com") return new Response(JSON.stringify({ Answer: [{ type: 1, data: "1.1.1.1" }] }), { status: 200 });
    throw new Error("unexpected lookup " + input);
  };
  try {
    const ready = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://example.com/")), {});
    assert.equal(ready.status, 200);
    assert.equal((await ready.json()).query, "https://example.com/");
  } finally {
    globalThis.fetch = original;
  }

  const stats = await worker.fetch(new Request("https://api.agentscouthq.com/stats", {
    headers: { ...site, "x-stats-key": "correct-key" },
  }), { ...binding, STATS_KEY: "correct-key" });
  assert.equal(stats.status, 200);
  assert.equal((await stats.json()).path, "/stats");
  assert.deepEqual(seen, [
    "POST /review",
    "GET /reviews",
    "GET /reviews/all",
    "POST /submit",
    "POST /generate",
    "GET /generate",
    "GET /track",
    "GET /geo",
    "GET /share",
    "POST /share",
    "GET /readiness",
    "GET /stats",
  ]);
});

test("review and track bodies, readiness URLs, and admin CORS stay bounded", async () => {
  const calls = [];
  const worker = protect({
    async fetch(request) {
      calls.push(new URL(request.url).pathname);
      if (new URL(request.url).pathname === "/track" && request.headers.get("x-throw") === "1") {
        throw new Error("internal token=super-secret");
      }
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json", "access-control-allow-origin": "*" },
      });
    },
  });
  const binding = env();
  const site = { origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.60", "content-type": "application/json" };
  const bigReview = await worker.fetch(new Request("https://api.agentscouthq.com/review", {
    method: "POST",
    headers: site,
    body: JSON.stringify({ tool: "cursor", text: "x".repeat(40_000) }),
  }), binding);
  assert.equal(bigReview.status, 413);
  assert.deepEqual(await bigReview.json(), { error: "Payload too large." });
  assert.equal(bigReview.headers.get("x-content-type-options"), "nosniff");
  assert.equal(calls.length, 0);

  const submit = await worker.fetch(new Request("https://api.agentscouthq.com/submit", {
    method: "POST",
    headers: { ...site, "content-type": "text/plain" },
    body: "x".repeat(50_000),
  }), binding);
  assert.equal(submit.status, 200);
  assert.deepEqual(calls, ["/submit"]);

  const bigTrack = await worker.fetch(new Request("https://api.agentscouthq.com/track", {
    method: "POST",
    headers: { "content-type": "text/plain", "cf-connecting-ip": "203.0.113.60" },
    body: "y".repeat(70_000),
  }), {});
  assert.equal(bigTrack.status, 413);
  assert.equal(calls.length, 1);

  const original = globalThis.fetch;
  let lookups = 0;
  globalThis.fetch = async () => { lookups += 1; throw new Error("dns"); };
  try {
    const long = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://example.com/" + "a".repeat(5000))), {});
    assert.equal(long.status, 400);
    assert.equal((await long.json()).error, "That address is not a valid URL.");
    assert.equal(lookups, 0);
  } finally {
    globalThis.fetch = original;
  }

  const limited = env();
  limited.IMAGE_READ = limiter(1);
  const first = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("http://127.0.0.1/"), {
    headers: { "cf-connecting-ip": "203.0.113.61" },
  }), limited);
  assert.equal(first.status, 400);
  const second = await worker.fetch(new Request("https://api.agentscouthq.com/readiness", {
    headers: { "cf-connecting-ip": "203.0.113.61" },
  }), limited);
  assert.equal(second.status, 429);
  const open = await worker.fetch(new Request("https://api.agentscouthq.com/readiness"), {});
  assert.equal(open.status, 200);

  const statsBinding = { ...env(), STATS_KEY: "correct-key" };
  const foreign = await worker.fetch(new Request("https://api.agentscouthq.com/stats", {
    headers: { "x-stats-key": "correct-key", origin: "https://evil.example", "cf-connecting-ip": "203.0.113.62" },
  }), statsBinding);
  assert.equal(foreign.status, 200);
  assert.equal(foreign.headers.get("access-control-allow-origin"), null);
  const home = await worker.fetch(new Request("https://api.agentscouthq.com/trending/stats", {
    headers: { "x-stats-key": "correct-key", origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.62" },
  }), statsBinding);
  assert.equal(home.status, 200);
  assert.equal(home.headers.get("access-control-allow-origin"), "https://agentscouthq.com");
  assert.equal(home.headers.get("x-frame-options"), "DENY");

  const boom = await worker.fetch(new Request("https://api.agentscouthq.com/track", {
    headers: { "x-throw": "1" },
  }), {});
  assert.equal(boom.status, 500);
  const boomText = await boom.text();
  assert.equal(boomText.includes("super-secret"), false);
  assert.deepEqual(JSON.parse(boomText), { error: "The request failed." });
});

test("the turnstile flag is masked only on the paths protect already checks", () => {
  const envBinding = { TURNSTILE_ENABLED: "true", TURNSTILE_SECRET: "turnstile-secret", IMAGE_WRITE: "binding" };
  const generate = maskTurnstileEnv(post("/generate"), envBinding);
  assert.equal(generate.TURNSTILE_ENABLED, "false");
  assert.equal(generate.TURNSTILE_SECRET, "turnstile-secret");
  assert.equal(generate.IMAGE_WRITE, "binding");
  const submit = maskTurnstileEnv(post("/submit"), envBinding);
  assert.equal(submit.TURNSTILE_ENABLED, "false");
  const review = maskTurnstileEnv(post("/review"), envBinding);
  assert.equal(review, envBinding);
  assert.equal(review.TURNSTILE_ENABLED, "true");
  const get = maskTurnstileEnv(new Request("https://api.agentscouthq.com/generate"), envBinding);
  assert.equal(get, envBinding);
});
