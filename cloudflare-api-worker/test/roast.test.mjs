import test, { describe } from "node:test";
import assert from "node:assert/strict";
import worker from "../src/worker.js";

const MAX_BYTES = 512_000;

function kv() {
  const store = new Map();
  return {
    async get(key) { return store.has(key) ? store.get(key) : null; },
    async put(key, value) { store.set(key, String(value)); },
  };
}

function roast(url, ip, env = { VOTES: kv() }, headers = {}) {
  return worker.fetch(new Request("https://votes.agentscouthq.com/roast", {
    method: "POST",
    headers: { "content-type": "application/json", ...(ip ? { "cf-connecting-ip": ip } : {}), ...headers },
    body: JSON.stringify({ url }),
  }), env);
}

function dns(ip) {
  return new Response(JSON.stringify({ Answer: [{ data: ip }] }), {
    status: 200,
    headers: { "content-type": "application/dns-json" },
  });
}

describe("roast body limit", { concurrency: false }, () => {
  test("a page larger than MAX_BYTES is scored from the head", async () => {
    const title = "Cursor The AI Code Editor";
    const pitch = "Agents write and review code in the repository beside the editor you already use daily.";
    assert.ok(title.length >= 15 && title.length <= 70);
    assert.ok(pitch.length >= 50 && pitch.length <= 160);
    const head = `<!doctype html><html><head><title>${title}</title>`
      + `<meta name="description" content="${pitch}">`
      + `<meta property="og:image" content="https://cursor.com/opengraph.png">`
      + `<script type="application/ld+json">{"@type":"SoftwareApplication"}</script>`
      + `</head><body><h1>${title}</h1>`;
    const filler = "x".repeat(1_100_000);
    const tail = "<p>TAIL Pricing starts at $20/mo on the paid plan. Free tier.</p></body></html>";
    const html = head + filler + tail;
    const bytes = new TextEncoder().encode(html);
    assert.ok(bytes.length > MAX_BYTES);
    assert.ok(bytes.length > 1_000_000);

    const state = { pulled: 0, cancelled: false };
    const calls = [];
    const chunkSize = 32 * 1024;
    const previous = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      calls.push(url);
      if (url.startsWith("https://cloudflare-dns.com/")) return dns("1.1.1.1");
      if (url.endsWith("/llms.txt")) return new Response("missing", { status: 404, headers: { "content-type": "text/plain" } });
      if (url.includes("/api/tools.json")) return new Response("[]", { status: 200, headers: { "content-type": "application/json" } });
      const stream = new ReadableStream({
        pull(controller) {
          if (state.pulled >= bytes.length) {
            controller.close();
            return;
          }
          const end = Math.min(bytes.length, state.pulled + chunkSize);
          controller.enqueue(bytes.subarray(state.pulled, end));
          state.pulled = end;
        },
        cancel() { state.cancelled = true; },
      });
      return new Response(stream, {
        status: 200,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "content-length": String(bytes.length),
        },
      });
    };
    try {
      const res = await roast("https://large.example/", "203.0.113.40");
      assert.equal(res.status, 200);
      const body = await res.json();
      assert.equal(body.ok, true);
      assert.equal(body.final_url, "https://large.example/");
      assert.equal(body.title, title);
      assert.equal(body.pitch, pitch);
      assert.equal(body.checks.find((c) => c.id === "pricing").ok, false);
      assert.equal(body.checks.find((c) => c.id === "og").ok, true);
      assert.equal(body.checks.find((c) => c.id === "jsonld").ok, true);
      assert.equal(body.error, undefined);
      assert.equal(state.cancelled, true);
      const fetched = calls.filter((url) => !url.startsWith("https://cloudflare-dns.com/"));
      assert.equal(fetched.some((url) => url.includes("large.example")), false);
      assert.ok(fetched.includes("https://1.1.1.1/"));
      assert.ok(state.pulled < bytes.length);
      assert.ok(state.pulled <= MAX_BYTES + chunkSize * 2);
    } finally {
      globalThis.fetch = previous;
    }
  });

  test("private IPs are still rejected", async () => {
    const calls = [];
    const previous = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      calls.push(url);
      if (url.startsWith("https://cloudflare-dns.com/")) return dns("10.0.0.1");
      throw new Error("fetched " + url);
    };
    try {
      for (const url of ["http://127.0.0.1/", "http://10.1.2.3/admin", "http://169.254.169.254/latest/meta-data/"]) {
        const res = await roast(url, "203.0.113.41");
        assert.equal(res.status, 400, url);
        const body = await res.json();
        assert.equal(body.error, "That address is not public.");
        assert.equal(body.ok, undefined);
      }
      assert.equal(calls.length, 0);
      const resolved = await roast("https://internal.example/", "203.0.113.41");
      assert.equal(resolved.status, 400);
      const resolvedBody = await resolved.json();
      assert.equal(resolvedBody.error, "That host resolves to a blocked address.");
      assert.ok(calls.length > 0);
      assert.ok(calls.every((url) => url.startsWith("https://cloudflare-dns.com/")));
    } finally {
      globalThis.fetch = previous;
    }
  });

  test("an empty page is an error", async () => {
    const previous = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      if (url.startsWith("https://cloudflare-dns.com/")) return dns("1.1.1.1");
      if (url.endsWith("/llms.txt") || url.includes("/api/tools.json")) {
        throw new Error("should not fetch " + url);
      }
      return new Response("", { status: 200, headers: { "content-type": "text/html; charset=utf-8" } });
    };
    try {
      const res = await roast("https://empty.example/", "203.0.113.42");
      assert.equal(res.status, 400);
      const body = await res.json();
      assert.equal(body.error, "That page had nothing to score.");
      assert.equal(body.ok, undefined);
    } finally {
      globalThis.fetch = previous;
    }
  });

  test("a missing vote binding and a forwarded client address fail closed", async () => {
    const calls = [];
    const previous = globalThis.fetch;
    globalThis.fetch = async (input) => {
      calls.push(String(input));
      throw new Error("fetched " + input);
    };
    try {
      const missing = await roast("https://example.com/", "203.0.113.43", {});
      assert.equal(missing.status, 503);
      const forwarded = await roast("https://example.com/", "", { VOTES: kv() }, { "x-forwarded-for": "198.51.100.9" });
      assert.equal(forwarded.status, 403);
      const mapped = await roast("http://[0:0:0:0:0:ffff:a9fe:a9fe]/", "203.0.113.43");
      assert.equal(mapped.status, 400);
      assert.equal((await mapped.json()).error, "That address is not public.");
      assert.deepEqual(calls, []);
    } finally {
      globalThis.fetch = previous;
    }
  });

  test("the page fetch uses the accepted address and a foreign peer fails closed", async () => {
    const calls = [];
    const previous = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = String(input);
      calls.push(url);
      if (url.startsWith("https://cloudflare-dns.com/")) return dns("1.1.1.1");
      const response = new Response("<title>Example</title>", { status: 200 });
      Object.defineProperty(response, "peerAddress", { value: "10.0.0.1" });
      return response;
    };
    try {
      const res = await roast("https://pinned.example/", "203.0.113.44");
      assert.equal(res.status, 400);
      assert.equal((await res.json()).error, "That host resolves to a blocked address.");
      const fetched = calls.filter((url) => !url.startsWith("https://cloudflare-dns.com/"));
      assert.ok(fetched.includes("https://1.1.1.1/"));
      assert.equal(fetched.some((url) => url.includes("pinned.example")), false);
    } finally {
      globalThis.fetch = previous;
    }
  });
});
