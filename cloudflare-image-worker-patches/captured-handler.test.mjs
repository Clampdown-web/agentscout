import test, { describe } from "node:test";
import assert from "node:assert/strict";
import { capturedReadinessGet } from "./captured-readiness-get.js";
import { capturedReadyAllowed, capturedReviewAllowed, capturedTrackAllowed } from "./captured-limiters.js";
import { protect } from "./security.js";

function limiter(max = 10) {
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

function dnsFetch(network, records) {
  return async (input) => {
    const url = String(input instanceof Request ? input.url : input);
    if (url.startsWith("https://cloudflare-dns.com/")) {
      const name = new URL(url).searchParams.get("name");
      const answer = records[name];
      if (answer === "down") return new Response("no", { status: 503 });
      return new Response(JSON.stringify({ Answer: [{ type: 1, data: answer || "1.1.1.1" }] }), { status: 200 });
    }
    network.push(url);
    if (url === "https://good.example/") {
      return new Response(null, { status: 302, headers: { location: "https://rebind.example/secret" } });
    }
    if (url === "https://good.example/next") {
      return new Response(null, { status: 302, headers: { location: "https://also.example/page" } });
    }
    return new Response("page", { status: 200, headers: { "content-type": "text/plain" } });
  };
}

describe("captured image handler", { concurrency: false }, () => {
test("the captured readiness loop fetches a redirected hostname with no DNS check", async () => {
  const original = globalThis.fetch;
  const network = [];
  globalThis.fetch = async (input) => {
    const url = String(input);
    network.push(url);
    if (url === "https://good.example/") {
      return new Response(null, { status: 302, headers: { location: "https://rebind.example/" } });
    }
    return new Response("fetched", { status: 200, headers: { "content-type": "text/plain" } });
  };
  try {
    const result = await capturedReadinessGet("https://good.example/");
    assert.equal(result.status, 200);
    assert.equal(result.text, "fetched");
    assert.ok(network.some((url) => url.includes("rebind.example")));
  } finally {
    globalThis.fetch = original;
  }
});

test("protect resolves each readiness redirect hop and does not fetch a private one", async () => {
  const original = globalThis.fetch;
  const network = [];
  globalThis.fetch = dnsFetch(network, { "good.example": "1.1.1.1", "rebind.example": "10.0.0.1" });
  const calls = [];
  const worker = protect({
    async fetch(request) {
      calls.push(new URL(request.url).pathname);
      const target = new URL(request.url).searchParams.get("url");
      return Response.json(await capturedReadinessGet(target));
    },
  });
  try {
    const response = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://good.example/")));
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.equal(body.err, "unreachable");
    assert.deepEqual(network, ["https://good.example/"]);
    assert.deepEqual(calls, ["/readiness"]);
  } finally {
    globalThis.fetch = original;
  }
});

test("a public readiness redirect is fetched, and a failed lookup is not", async () => {
  const original = globalThis.fetch;
  const network = [];
  globalThis.fetch = dnsFetch(network, { "good.example": "1.1.1.1", "also.example": "1.1.1.1", "down.example": "down" });
  const worker = protect({
    async fetch() {
      return Response.json(await capturedReadinessGet("https://good.example/next"));
    },
  });
  try {
    const ok = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://good.example/next")));
    const body = await ok.json();
    assert.equal(body.status, 200);
    assert.equal(body.final, "https://also.example/page");
    assert.deepEqual(network, ["https://good.example/next", "https://also.example/page"]);
    network.length = 0;
    const denied = await worker.fetch(new Request("https://api.agentscouthq.com/readiness?url=" + encodeURIComponent("https://down.example/")));
    assert.equal(denied.status, 400);
    assert.deepEqual(network, []);
  } finally {
    globalThis.fetch = original;
  }
});

test("captured limiter catches stay fail-closed when the binding throws and still allow a real success", async () => {
  const original = globalThis.fetch;
  let fetches = 0;
  globalThis.fetch = async () => { fetches += 1; throw new Error("inner should not fetch"); };
  const worker = protect({
    async fetch(request, binding) {
      const path = new URL(request.url).pathname;
      if (path === "/review") { const status = await capturedReviewAllowed(binding); return new Response(String(status), { status }); }
      if (path === "/track") { const status = await capturedTrackAllowed(binding); return new Response(String(status), { status }); }
      if (path === "/readiness") { const status = await capturedReadyAllowed(binding); return new Response(String(status), { status }); }
      return new Response("no", { status: 500 });
    },
  });
  const headers = { origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.10", "content-type": "application/json" };
  try {
    const review = await worker.fetch(new Request("https://api.agentscouthq.com/review", { method: "POST", headers, body: "{}" }), {
      ...env(),
      REVIEW_RL: { async limit() { throw new Error("review limiter down"); } },
    });
    assert.equal(review.status, 429);
    const reviewOk = await worker.fetch(new Request("https://api.agentscouthq.com/review", { method: "POST", headers, body: "{}" }), {
      ...env(),
      REVIEW_RL: { async limit() { return { success: true }; } },
    });
    assert.equal(reviewOk.status, 200);
    const reviewMissing = await worker.fetch(new Request("https://api.agentscouthq.com/review", { method: "POST", headers, body: "{}" }), env());
    assert.equal(reviewMissing.status, 200);
    const track = await worker.fetch(new Request("https://api.agentscouthq.com/track", { method: "POST" }), {
      TRACK_RL: { async limit() { throw new Error("track limiter down"); } },
    });
    assert.equal(track.status, 429);
    const ready = await worker.fetch(new Request("https://api.agentscouthq.com/readiness"), {
      READY_LIMIT: {
        idFromName() { return "id"; },
        get() { return { async fetch() { throw new Error("ready object down"); } }; },
      },
    });
    assert.equal(ready.status, 429);
    const readyOk = await worker.fetch(new Request("https://api.agentscouthq.com/readiness"), {
      READY_LIMIT: {
        idFromName() { return "id"; },
        get() { return { async fetch() { return Response.json({ ok: true, left: 9 }); } }; },
      },
    });
    assert.equal(readyOk.status, 200);
    const readyRl = await worker.fetch(new Request("https://api.agentscouthq.com/readiness"), {
      READY_RL: { async limit() { throw new Error("ready limiter down"); } },
    });
    assert.equal(readyRl.status, 429);
    assert.equal(fetches, 0);
  } finally {
    globalThis.fetch = original;
  }
});
});
