import test from "node:test";
import assert from "node:assert/strict";
import worker from "../worker.js";

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
  return { MCP_BURST: limiter(15), MCP_MINUTE: limiter(60) };
}

function hit(headers = {}, cf) {
  const request = new Request("https://mcp.agentscouthq.com/mcp", {
    method: "GET",
    headers: { "cf-connecting-ip": "203.0.113.8", ...headers },
  });
  if (cf) Object.defineProperty(request, "cf", { value: cf });
  return request;
}

test("15 requests pass and the 16th is 429, including a Googlebot user-agent", async () => {
  const binding = env();
  let last = 0;
  for (let i = 0; i < 16; i++) {
    const res = await worker.fetch(hit({
      "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    }), binding);
    last = res.status;
    if (i < 15) assert.equal(res.status, 200);
  }
  assert.equal(last, 429);
  const body = await (await worker.fetch(hit({
    "user-agent": "Googlebot",
  }), binding)).json();
  assert.match(body.error, /Too many requests/);
});

test("a second IP has its own counter", async () => {
  const binding = env();
  for (let i = 0; i < 15; i++) await worker.fetch(hit(), binding);
  const blocked = await worker.fetch(hit(), binding);
  assert.equal(blocked.status, 429);
  const other = await worker.fetch(hit({ "cf-connecting-ip": "203.0.113.9" }), binding);
  assert.equal(other.status, 200);
});

test("Cloudflare verified-bot fields skip the limiter; an empty category does not", async () => {
  const binding = env();
  for (let i = 0; i < 15; i++) assert.equal((await worker.fetch(hit(), binding)).status, 200);
  assert.equal((await worker.fetch(hit({}, { verifiedBotCategory: "", botManagement: { verifiedBot: false } }), binding)).status, 429);
  assert.equal((await worker.fetch(hit({}, { verifiedBotCategory: "  " }), binding)).status, 429);
  assert.equal((await worker.fetch(hit({ "user-agent": "NotABot" }, { verifiedBotCategory: "Search Engine Crawler" }), binding)).status, 200);
  assert.equal((await worker.fetch(hit({ "user-agent": "Googlebot" }, { botManagement: { verifiedBot: true } }), binding)).status, 200);
});

test("X-Forwarded-For is not the client address", async () => {
  const keys = [];
  const binding = {
    MCP_BURST: { async limit({ key }) { keys.push(key); return { success: true }; } },
    MCP_MINUTE: { async limit({ key }) { keys.push(key); return { success: true }; } },
  };
  const res = await worker.fetch(hit({ "x-forwarded-for": "198.51.100.9" }), binding);
  assert.equal(res.status, 200);
  assert.deepEqual(keys, ["203.0.113.8", "203.0.113.8"]);
  const missing = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    headers: { "x-forwarded-for": "198.51.100.9" },
  }), binding);
  assert.equal(missing.status, 403);
  assert.equal(keys.length, 2);
});

test("a thrown limiter and a minute rejection fail closed", async () => {
  const thrown = await worker.fetch(hit(), {
    MCP_BURST: { async limit() { throw new Error("binding down"); } },
    MCP_MINUTE: { async limit() { return { success: true }; } },
  });
  assert.equal(thrown.status, 503);
  const thrownBody = await thrown.json();
  assert.equal(thrownBody.error, "Rate limiting is not configured.");
  assert.equal(thrownBody.tools, undefined);
  assert.equal(thrownBody.tools_indexed, undefined);
  const minute = await worker.fetch(hit(), {
    MCP_BURST: { async limit() { return { success: true }; } },
    MCP_MINUTE: { async limit() { return { success: false }; } },
  });
  assert.equal(minute.status, 429);
});

test("wildcard CORS stays on read responses and credentials are not allowed", async () => {
  const res = await worker.fetch(hit(), env());
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  assert.equal(res.headers.get("access-control-allow-credentials"), null);
  const body = await res.json();
  assert.equal(body.read_only, true);
});

test("a missing binding fails closed and does not serve the catalog", async () => {
  const res = await worker.fetch(hit({ "user-agent": "Googlebot" }, {
    verifiedBotCategory: "Search Engine Crawler",
  }), {});
  assert.equal(res.status, 503);
  const body = await res.json();
  assert.equal(body.error, "Rate limiting is not configured.");
  assert.equal(body.tools, undefined);
});
