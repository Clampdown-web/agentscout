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
  assert.equal(JSON.stringify(thrownBody).includes("binding down"), false);
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

test("public MCP routes keep status, JSON-RPC shape, registry shape, and CORS", async () => {
  const binding = { MCP_BURST: limiter(100), MCP_MINUTE: limiter(100) };
  const headers = { "cf-connecting-ip": "203.0.113.40" };
  const preflight = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "OPTIONS",
    headers,
  }), binding);
  assert.equal(preflight.status, 204);
  assert.equal(await preflight.text(), "");
  assert.equal(preflight.headers.get("access-control-allow-origin"), "*");
  assert.equal(preflight.headers.get("access-control-allow-credentials"), null);
  assert.equal(preflight.headers.get("access-control-allow-methods"), "POST, GET, OPTIONS");
  assert.match(preflight.headers.get("access-control-allow-headers"), /Mcp-Protocol-Version/);
  assert.equal(preflight.headers.get("x-content-type-options"), "nosniff");
  assert.equal(preflight.headers.get("x-frame-options"), "DENY");

  const info = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", { headers }), binding);
  assert.equal(info.status, 200);
  assert.equal(info.headers.get("content-type"), "application/json; charset=utf-8");
  assert.equal(info.headers.get("cache-control"), "no-store");
  assert.equal(info.headers.get("access-control-allow-origin"), "*");
  const infoBody = await info.json();
  assert.equal(infoBody.name, "AgentScout MCP server");
  assert.equal(infoBody.endpoint, "https://mcp.agentscouthq.com/mcp");
  assert.equal(infoBody.transport, "streamable-http");
  assert.equal(infoBody.read_only, true);
  assert.ok(infoBody.tools.includes("search_tools"));
  assert.ok(infoBody.tools.includes("get_tool"));
  assert.ok(infoBody.tools.includes("list_categories"));
  assert.ok(infoBody.tools.includes("best_for_task"));
  assert.ok(infoBody.tools.includes("list_packages"));
  assert.equal(typeof infoBody.tools_indexed, "number");

  const root = await worker.fetch(new Request("https://mcp.agentscouthq.com/", { headers }), binding);
  assert.equal(root.status, 200);
  assert.equal((await root.json()).read_only, true);

  const registry = await worker.fetch(new Request("https://mcp.agentscouthq.com/v0/servers?search=com.agentscouthq", { headers }), binding);
  assert.equal(registry.status, 200);
  const registryBody = await registry.json();
  assert.equal(registryBody.metadata.count, 1);
  assert.equal(registryBody.servers[0].server.name, "com.agentscouthq/directory");
  assert.equal(registryBody.servers[0].server.remotes[0].url, "https://mcp.agentscouthq.com/mcp");

  function rpc(message) {
    return worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
      method: "POST",
      headers: { ...headers, "content-type": "application/json" },
      body: JSON.stringify(message),
    }), binding);
  }

  const init = await rpc({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "0" } } });
  assert.equal(init.status, 200);
  assert.equal(init.headers.get("x-content-type-options"), "nosniff");
  assert.match(init.headers.get("x-ratelimit-limit"), /60/);
  const initBody = await init.json();
  assert.equal(initBody.jsonrpc, "2.0");
  assert.equal(initBody.id, 1);
  assert.equal(initBody.result.protocolVersion, "2025-06-18");
  assert.equal(initBody.result.serverInfo.name, "agentscout");
  assert.equal(initBody.result.capabilities.tools.listChanged, false);
  assert.equal(typeof initBody.result.instructions, "string");

  const ping = await rpc({ jsonrpc: "2.0", id: "ping-1", method: "ping" });
  assert.equal(ping.status, 200);
  assert.deepEqual(await ping.json(), { jsonrpc: "2.0", id: "ping-1", result: {} });

  const list = await rpc({ jsonrpc: "2.0", id: 2, method: "tools/list" });
  const listBody = await list.json();
  assert.equal(list.status, 200);
  assert.deepEqual(listBody.result.tools.map((tool) => tool.name), ["search_tools", "get_tool", "list_categories", "best_for_task", "list_packages"]);

  const search = await rpc({ jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "search_tools", arguments: { query: "siena", limit: 2 } } });
  assert.equal(search.status, 200);
  const searchBody = await search.json();
  assert.equal(searchBody.result.isError, false);
  assert.equal(searchBody.result.structuredContent.results[0].slug, "siena-social-agent");
  assert.equal(searchBody.result.structuredContent.results.length <= 2, true);
  assert.equal(typeof searchBody.result.structuredContent.total_matches, "number");
  assert.equal(searchBody.result.content[0].type, "text");

  const one = await rpc({ jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "get_tool", arguments: { slug: "siena-social-agent" } } });
  const oneBody = await one.json();
  assert.equal(oneBody.result.isError, false);
  assert.equal(oneBody.result.structuredContent.tool.slug, "siena-social-agent");
  assert.equal(oneBody.result.structuredContent.tool.name, "Siena Social Agent");

  const task = await rpc({ jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "best_for_task", arguments: { task: "social agent", limit: 1 } } });
  const taskBody = await task.json();
  assert.equal(taskBody.result.isError, false);
  assert.equal(taskBody.result.structuredContent.results.length, 1);

  const cats = await rpc({ jsonrpc: "2.0", id: 6, method: "tools/call", params: { name: "list_categories", arguments: {} } });
  const catsBody = await cats.json();
  assert.ok(catsBody.result.structuredContent.categories.length > 0);
  assert.equal(typeof catsBody.result.structuredContent.categories[0].name, "string");
  assert.equal(typeof catsBody.result.structuredContent.categories[0].tools, "number");

  const packs = await rpc({ jsonrpc: "2.0", id: 7, method: "tools/call", params: { name: "list_packages", arguments: { category: "listing_package" } } });
  const packsBody = await packs.json();
  assert.equal(packsBody.result.isError, false);
  assert.ok(packsBody.result.structuredContent.products.length >= 1);
  assert.ok(packsBody.result.structuredContent.products.every((item) => item.group === "listing_package"));
  const addons = await rpc({ jsonrpc: "2.0", id: 8, method: "tools/call", params: { name: "list_packages", arguments: { category: "addon" } } });
  const addonsBody = await addons.json();
  assert.equal(addonsBody.result.isError, false);
  assert.deepEqual(addonsBody.result.structuredContent.products, []);

  const note = await rpc({ jsonrpc: "2.0", method: "notifications/initialized" });
  assert.equal(note.status, 202);
  assert.equal(await note.text(), "");

  const bad = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "POST",
    headers: { ...headers, "content-type": "application/json" },
    body: "{",
  }), binding);
  assert.equal(bad.status, 400);
  assert.deepEqual(await bad.json(), { jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });

  const missingMethod = await rpc({ jsonrpc: "2.0", id: 9, method: "no_such_method" });
  assert.equal(missingMethod.status, 200);
  assert.deepEqual(await missingMethod.json(), { jsonrpc: "2.0", id: 9, error: { code: -32601, message: "Method not found: no_such_method" } });

  const denied = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "PUT",
    headers,
  }), binding);
  assert.equal(denied.status, 405);
  assert.equal(denied.headers.get("allow"), "GET, POST, OPTIONS");
  assert.deepEqual(await denied.json(), { error: "Method not allowed" });
});

test("oversized MCP bodies, queries, and tool arguments are rejected", async () => {
  const binding = { MCP_BURST: limiter(20), MCP_MINUTE: limiter(20) };
  const headers = { "cf-connecting-ip": "203.0.113.41", "content-type": "application/json" };
  const huge = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "POST",
    headers,
    body: "x".repeat(100_001),
  }), binding);
  assert.equal(huge.status, 413);
  assert.deepEqual(await huge.json(), { error: "Payload too large" });

  const empty = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "POST",
    headers,
    body: "null",
  }), binding);
  assert.equal(empty.status, 400);
  const emptyBody = await empty.json();
  assert.deepEqual(emptyBody, { jsonrpc: "2.0", id: null, error: { code: -32600, message: "Invalid Request" } });
  assert.equal(JSON.stringify(emptyBody).includes("stack"), false);

  const longQuery = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "search_tools", arguments: { query: "a".repeat(201) } } }),
  }), binding);
  assert.equal(longQuery.status, 200);
  const longBody = await longQuery.json();
  assert.equal(longBody.result.isError, true);
  assert.match(longBody.result.structuredContent.error, /200/);
  assert.equal(JSON.stringify(longBody).includes("a".repeat(201)), false);

  const longTask = await worker.fetch(new Request("https://mcp.agentscouthq.com/mcp", {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: "best_for_task", arguments: { task: "ab" + "c".repeat(200) } } }),
  }), binding);
  assert.equal((await longTask.json()).result.isError, true);

  const wide = "https://mcp.agentscouthq.com/v0/servers?search=" + "q".repeat(9000);
  const query = await worker.fetch(new Request(wide, { headers }), binding);
  assert.equal(query.status, 400);
  assert.deepEqual(await query.json(), { error: "Query too large" });
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
