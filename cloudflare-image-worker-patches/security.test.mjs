import test from "node:test";
import assert from "node:assert/strict";
import { allowOrigin, postAllowed, guardedKind, maskTurnstileEnv, protect, safeEq, statsKeyPath, turnstileEnabled } from "./security.js";

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
    if (token === "good") return new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com" }));
    if (token === "www") return new Response(JSON.stringify({ success: true, hostname: "www.agentscouthq.com" }));
    if (token === "wrong-host") return new Response(JSON.stringify({ success: true, hostname: "evil.example" }));
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

test("protect masks TURNSTILE_ENABLED only after it has checked submit and generate", async () => {
  await withSiteverify(() => new Response(JSON.stringify({ success: true, hostname: "agentscouthq.com" })), async () => {
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
