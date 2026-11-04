import test from "node:test";
import assert from "node:assert/strict";
import { allowOrigin, postAllowed, guardedKind, protect } from "./security.js";

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
  assert.equal(guardedKind("/generate"), "");
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

function post(path, headers = {}) {
  return new Request("https://api.agentscouthq.com" + path, {
    method: "POST",
    headers: { "content-type": "text/plain", "cf-connecting-ip": "203.0.113.10", ...headers },
    body: "{}",
  });
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

test("/generate is not wrapped", async () => {
  const { worker, calls } = handler();
  const res = await worker.fetch(new Request("https://api.agentscouthq.com/generate", {
    method: "POST",
    headers: { origin: "https://evil.example", "content-type": "text/plain" },
    body: "{}",
  }), {});
  assert.equal(res.status, 200);
  assert.deepEqual(calls, ["/generate"]);
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
});
