import test from "node:test";
import assert from "node:assert/strict";
import worker from "../src/worker.js";

function kv() {
  const store = new Map();
  return {
    async get(key) { return store.has(key) ? store.get(key) : null; },
    async put(key, value) { store.set(key, String(value)); },
  };
}

function publicFetch() {
  return async (input) => {
    const url = String(input);
    if (url.startsWith("https://cloudflare-dns.com/")) {
      return new Response(JSON.stringify({ Answer: [{ type: 1, data: "1.1.1.1" }] }), { status: 200 });
    }
    if (url.endsWith("/llms.txt")) return new Response("missing", { status: 404 });
    if (url.includes("/api/tools.json")) return new Response("[]", { status: 200 });
    return new Response("<title>Example Public Tool Listing For The Roast</title><p>Free plan.</p>", {
      status: 200,
      headers: { "content-type": "text/html" },
    });
  };
}

test("parallel roast requests in one isolate stay inside the per-minute cap", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = publicFetch();
  try {
    const env = { VOTES: kv() };
    const responses = await Promise.all(Array.from({ length: 20 }, () => worker.fetch(new Request("https://votes.agentscouthq.com/roast", {
      method: "POST",
      headers: { "content-type": "application/json", origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.77" },
      body: JSON.stringify({ url: "https://example.com/" }),
    }), env)));
    const statuses = await Promise.all(responses.map((res) => res.status));
    const allowed = statuses.filter((status) => status === 200).length;
    const limited = statuses.filter((status) => status === 429).length;
    assert.equal(allowed, 8);
    assert.equal(limited, 12);
  } finally {
    globalThis.fetch = original;
  }
});

test("roast and vote fail closed without the KV binding", async () => {
  const original = globalThis.fetch;
  let fetched = false;
  globalThis.fetch = async () => { fetched = true; throw new Error("should not fetch"); };
  try {
    const roast = await worker.fetch(new Request("https://votes.agentscouthq.com/roast?url=https://example.com/", {
      headers: { origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.78" },
    }), {});
    assert.equal(roast.status, 503);
    const vote = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
      method: "POST",
      headers: { "content-type": "application/json", origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.78" },
      body: JSON.stringify({ slug: "cursor" }),
    }), {});
    assert.equal(vote.status, 503);
    assert.equal(fetched, false);
  } finally {
    globalThis.fetch = original;
  }
});

test("optional rate limit bindings fail closed and do not write the KV counter", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = publicFetch();
  const puts = [];
  const store = {
    async get() { return null; },
    async put(key) { puts.push(key); },
  };
  const roast = (env) => worker.fetch(new Request("https://votes.agentscouthq.com/roast", {
    method: "POST",
    headers: { "content-type": "application/json", origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.79" },
    body: JSON.stringify({ url: "https://example.com/" }),
  }), env);
  try {
    const denied = await roast({
      VOTES: store,
      ROAST_RL: { async limit() { return { success: false }; } },
    });
    assert.equal(denied.status, 429);
    const thrown = await roast({
      VOTES: store,
      ROAST_RL: { async limit() { throw new Error("limiter down"); } },
    });
    assert.equal(thrown.status, 429);
    const vote = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
      method: "POST",
      headers: { "content-type": "application/json", origin: "https://agentscouthq.com", "cf-connecting-ip": "203.0.113.79" },
      body: "{}",
    }), { VOTES: store, VOTE_RL: { async limit() { return {}; } } });
    assert.equal(vote.status, 429);
    const allowed = await roast({
      VOTES: store,
      ROAST_RL: { async limit() { return { success: true }; } },
    });
    assert.equal(allowed.status, 200);
    assert.deepEqual(puts.filter((key) => key.startsWith("rl:")), []);
  } finally {
    globalThis.fetch = original;
  }
});
