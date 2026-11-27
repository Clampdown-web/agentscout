/**
 * AgentScout read-only MCP worker.
 * Commerce data comes from products_snapshot.json.
 * The tool catalog is fetched from https://agentscouthq.com/api/tools.json and
 * cached for 10 minutes, so a site build refreshes search without another deploy.
 * catalog_snapshot.json is the fallback when that fetch fails.
 *
 * Every response gets the security headers below. Burst (15 / 10s) and per-minute
 * (60 / 60s) caps use the Workers Rate Limiting bindings MCP_BURST and MCP_MINUTE,
 * keyed by CF-Connecting-IP. Those counters are shared across isolates in a
 * Cloudflare location. A User-Agent string is never a bypass. A request is exempt
 * only when Cloudflare sets request.cf.verifiedBotCategory or
 * request.cf.botManagement.verifiedBot.
 */
import catalog from "./catalog_snapshot.json" with { type: "json" };
import products from "./products_snapshot.json" with { type: "json" };

const SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
  "Referrer-Policy": "strict-origin-when-cross-origin",
};

// Desktop and server MCP clients ignore CORS. The site does not call this host
// from the browser. A wildcard without credentials keeps browser MCP clients working.
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Protocol-Version, Mcp-Session-Id, X-AgentScout-Test",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Max-Age": "86400",
};

const BURST_WINDOW_MS = 10_000;
const BURST_MAX = 15;
const MINUTE_WINDOW_MS = 60_000;
const MINUTE_MAX = 60;
const MAX_BODY = 100_000;
const MAX_QUERY = 8_192;
const MAX_IP_LEN = 128;
const MAX_RPC_ID = 256;
const MAX_METHOD = 128;

const BUNDLED_TOOLS = Array.isArray(catalog.tools) ? catalog.tools : [];
const BUNDLED_BY_SLUG = new Map(BUNDLED_TOOLS.map((tool) => [tool.slug, tool]));
const CATALOG_URL = "https://agentscouthq.com/api/tools.json";
const CATALOG_TTL_MS = 10 * 60 * 1000;
let catalogMemory = null;

function bundledView() {
  return {
    updated: pacificIso(catalog.updated),
    last_checked: catalog.last_checked,
    count: catalog.count,
    category_count: catalog.category_count,
    mcp_count: catalog.mcp_count,
    tools: BUNDLED_TOOLS,
    bySlug: BUNDLED_BY_SLUG,
    source: "bundle",
  };
}

function pacificIso(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return String(value || "");
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
    timeZoneName: "longOffset",
  }).formatToParts(date);
  const get = (type) => parts.find((part) => part.type === type)?.value || "";
  let offset = get("timeZoneName").replace(/^GMT/i, "");
  const match = offset.match(/^([+-])(\d{1,2})(?::(\d{2}))?$/);
  if (match) offset = `${match[1]}${match[2].padStart(2, "0")}:${match[3] || "00"}`;
  else offset = "-08:00";
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}:${get("second")}${offset}`;
}

function classifyLocality(tool) {
  if (tool.data_locality) return tool.data_locality;
  const cat = String(tool.category || "").toLowerCase();
  const tags = (tool.tags || []).map((tag) => String(tag).toLowerCase());
  const plats = tool.platforms || [];
  const blob = `${tool.description || ""} ${tool.pricing || ""} ${tags.join(" ")}`;
  const openSrc = !!tool.open_source;
  const hasSelf = plats.includes("Self-host");
  const offline = /\b(runs?\s+locally|100%\s+local(?:ly)?|fully\s+local(?:ly)?|offline|on-device|on\s+your\s+(?:mac|pc|machine|computer|device|laptop)|local-first|ollama|lm\s*studio|llama\.cpp|gguf)\b/i;
  const selfHost = /\b(self-host(?:ed|able|ing)?|on-prem(?:ise|ises)?|docker|own\s+server|local\s+or\s+remote|stdio)\b/i;
  const cloud = /\b(hosted\s+service|managed\s+cloud|cloud-only|saas\s+platform)\b/i;
  if ((cat === "models & local runtimes" || tags.includes("local models") || tags.includes("offline") || offline.test(blob)) && !cloud.test(blob)) return "offline";
  if (hasSelf || tags.includes("self-hosting") || (openSrc && selfHost.test(blob))) return "self_hosted";
  if (!openSrc && !hasSelf && (plats.includes("Web") || cloud.test(blob))) return "cloud";
  return "unknown";
}

export function catalogFromApi(data) {
  const rows = Array.isArray(data?.tools) ? data.tools : [];
  const tools = rows.filter((row) => row && row.slug).map((row) => ({
    name: row.name,
    slug: row.slug,
    category: row.category,
    description: row.description || "",
    pricing: row.pricing || "",
    price_tag: row.price_tag || "unknown",
    open_source: !!row.open_source,
    github_stars: row.github_stars ?? null,
    website: row.website || row.url || "",
    page: row.page || "",
    key_features: row.key_features || [],
    platforms: row.platforms || [],
    tags: row.tags || [],
    github: row.github || null,
    license: row.license || null,
    date_added: row.date_added || row.added || "",
    data_locality: classifyLocality(row),
  }));
  const categories = [...new Set(tools.map((tool) => tool.category).filter(Boolean))].sort();
  const mcp = tools.filter((tool) => tool.category === "MCP servers").length;
  const checked = data?.last_checked;
  return {
    updated: pacificIso(data?.updated || data?.generated),
    last_checked: typeof checked === "string" && /^\d{4}-\d{2}-\d{2}$/.test(checked) ? checked : pacificIso(checked).slice(0, 10),
    count: tools.length,
    category_count: categories.length,
    mcp_count: mcp,
    tools,
    bySlug: new Map(tools.map((tool) => [tool.slug, tool])),
    source: "api",
  };
}

export async function loadCatalog(fetcher) {
  // Node tests have no Worker cache. They keep using the bundled snapshot.
  if (!fetcher && typeof caches === "undefined") return bundledView();
  const now = Date.now();
  if (catalogMemory && now - catalogMemory.at < CATALOG_TTL_MS) return catalogMemory.view;
  const fetchImpl = fetcher || fetch;
  try {
    const response = await fetchImpl(CATALOG_URL, { cf: { cacheTtl: 600, cacheEverything: true } });
    if (!response.ok) throw new Error(String(response.status));
    const data = await response.json();
    const view = catalogFromApi(data);
    if (!view.count) throw new Error("empty");
    catalogMemory = { at: now, view };
    return view;
  } catch {
    return catalogMemory ? catalogMemory.view : bundledView();
  }
}

const SERVER_INFO = {
  name: "agentscout",
  title: "AgentScout directory",
  version: "1.0.2",
};

const INSTRUCTIONS =
  "Read-only search over the AgentScout directory of AI agent tools and MCP servers (agentscouthq.com). Use search_tools or best_for_task, then get_tool for details. Pricing is as makers state it. For tools that must keep data on the user's machine or servers, pass runs_locally ('offline' or 'self_hosted_or_offline') and relay data_locality_note plus the caveat; locality is inferred from listings, so tell users to verify it for compliance. Cite the agentscout_url.";

const LOCALITY_CAVEAT =
  "Data locality is inferred from the listing text by AgentScout, not audited. Verify with the vendor before relying on it for compliance; some features may still call cloud APIs.";

const PRICE_NOTE = "Pricing is as each maker states it; confirm on the maker's site.";
const PACK_TIER_URLS = {
  tier_1: "https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
  tier_5: "https://buy.stripe.com/9B600kfpx4dhbtb8vxe7m0a",
  tier_25: "https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d",
};

const TOOL_DEFS = [
  {
    name: "search_tools",
    title: "Search AI agent tools",
    description:
      "Search the AgentScout directory of AI agent tools and MCP servers by keyword, with optional category, pricing, open-source and data-locality (runs_locally) filters. Each result has data_locality (offline, self_hosted, cloud or unknown) with a plain note. Returns up to 25 matches with pricing as the maker states it and the AgentScout listing URL.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: { type: "string", maxLength: 200, description: "Keywords, e.g. 'browser automation' or 'postgres'. Optional if a filter is set." },
        category: { type: "string", maxLength: 80, description: "Exact category name from list_categories, e.g. 'MCP servers'." },
        pricing: { type: "string", enum: ["any", "free", "freemium", "paid", "unknown"], description: "Pricing type. 'freemium' = free plan plus paid plans." },
        open_source: { type: "boolean", description: "true = only open-source tools." },
        runs_locally: { type: "string", enum: ["offline", "self_hosted_or_offline", "any"], description: "Where the tool can run, so data can stay on your side. 'offline' = runs fully on your own machine (e.g. with local models). 'self_hosted_or_offline' = also includes tools you can deploy on your own server. 'any' (default) = no filter. Based on what each listing says; tools without clear evidence are excluded from both filters." },
        limit: { type: "integer", minimum: 1, maximum: 25, description: "Max results (default 10)." },
      },
    },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true },
  },
  {
    name: "get_tool",
    title: "Get one tool",
    description: "Get the full AgentScout listing for one tool by its slug (from search_tools results), including key features, platforms, GitHub repo and stars, and data_locality with the evidence phrase.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["slug"],
      properties: {
        slug: { type: "string", pattern: "^[a-z0-9][a-z0-9-]{0,99}$", description: "Tool slug, e.g. 'cursor'." },
      },
    },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true },
  },
  {
    name: "list_categories",
    title: "List categories",
    description: "List every AgentScout category with its tool count and page URL.",
    inputSchema: { type: "object", additionalProperties: false, properties: {} },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true },
  },
  {
    name: "best_for_task",
    title: "Best tools for a task",
    description: "Suggest AgentScout tools for a task described in plain words (e.g. 'scrape websites with an agent'), ranked by relevance with listed GitHub stars as a tiebreak. Optional pricing, open-source and runs_locally filters; use runs_locally when data must stay on the user's machine or servers (e.g. 'no-code automation that runs locally').",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["task"],
      properties: {
        task: { type: "string", minLength: 2, maxLength: 200, description: "What you want to get done." },
        pricing: { type: "string", enum: ["any", "free", "freemium", "paid", "unknown"] },
        open_source: { type: "boolean" },
        runs_locally: { type: "string", enum: ["offline", "self_hosted_or_offline", "any"], description: "Where the tool can run, so data can stay on your side. 'offline' = runs fully on your own machine (e.g. with local models). 'self_hosted_or_offline' = also includes tools you can deploy on your own server. 'any' (default) = no filter. Based on what each listing says; tools without clear evidence are excluded from both filters." },
        limit: { type: "integer", minimum: 1, maximum: 10, description: "Max results (default 5)." },
      },
    },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true },
  },
  {
    name: "list_packages",
    title: "List AgentScout maker packages & pre-trained bots",
    description: "List AgentScout's 4 maker listing packages ($0, $15 Fast-Track with a same-day Google sitemap submission and a Bing and IndexNow ping, $49 category pin, $99/wk sponsor) and the Made by AgentScout pre-trained bot lineup. The $99 weekly sponsorship includes submissions to about 25 other AI directories. That work is not a separate listing tier.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        category: { type: "string", enum: ["all", "listing_package", "addon", "bot_template", "agent_pack"], description: "Filter by product category (default 'all'). Directory submissions come with the $99 weekly sponsor, not a separate addon." },
      },
    },
    annotations: { readOnlyHint: true, openWorldHint: false, idempotentHint: true },
  },
];

function securityHeaders(extra) {
  const headers = new Headers(extra || undefined);
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) headers.set(key, value);
  for (const [key, value] of Object.entries(CORS_HEADERS)) headers.set(key, value);
  return headers;
}

function jsonResponse(body, status = 200, extra) {
  const headers = securityHeaders(extra);
  headers.set("Content-Type", "application/json; charset=utf-8");
  headers.set("Cache-Control", "no-store");
  return new Response(JSON.stringify(body), { status, headers });
}

function emptyResponse(status, extra) {
  return new Response(null, { status, headers: securityHeaders(extra) });
}

function clientIp(request) {
  const ip = (request.headers.get("CF-Connecting-IP") || "").trim();
  if (!ip || ip.length > MAX_IP_LEN || /[\u0000-\u0020]/.test(ip)) return "";
  return ip;
}

function logToken(value) {
  return String(value ?? "").replace(/[\u0000-\u001f]/g, " ").slice(0, 80);
}

function plainObject(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

async function readCapped(request, max) {
  const declared = Number(request.headers.get("Content-Length"));
  if (Number.isFinite(declared) && declared > max) return { error: "too_large" };
  const reader = request.body?.getReader?.();
  if (!reader) {
    const text = typeof request.text === "function" ? await request.text() : "";
    if (text.length > max) return { error: "too_large" };
    return { text };
  }
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value?.byteLength) continue;
      size += value.byteLength;
      if (size > max) return { error: "too_large" };
      chunks.push(value);
    }
  } catch {
    return { error: "bad_body" };
  } finally {
    try { await reader.cancel(); } catch { /* already closed */ }
  }
  const buf = new Uint8Array(size);
  let off = 0;
  for (const chunk of chunks) { buf.set(chunk, off); off += chunk.byteLength; }
  return { text: new TextDecoder("utf-8", { fatal: false }).decode(buf) };
}

function rpcId(message) {
  if (!Object.prototype.hasOwnProperty.call(message, "id")) return { id: null };
  const id = message.id;
  if (id === null) return { id: null };
  if (typeof id === "number" && Number.isFinite(id)) return { id };
  if (typeof id === "string" && id.length <= MAX_RPC_ID && !/[\u0000-\u001f]/.test(id)) return { id };
  return { error: true };
}

// Cloudflare-verified crawlers only. A User-Agent of "Googlebot" is not evidence.
function verifiedCrawler(request) {
  const cf = request.cf;
  if (!cf || typeof cf !== "object") return false;
  const category = typeof cf.verifiedBotCategory === "string" ? cf.verifiedBotCategory.trim() : "";
  if (category) return true;
  const management = cf.botManagement;
  return !!(management && typeof management === "object" && management.verifiedBot === true);
}

function limitersReady(env) {
  return !!(env && env.MCP_BURST && typeof env.MCP_BURST.limit === "function"
    && env.MCP_MINUTE && typeof env.MCP_MINUTE.limit === "function");
}

async function rateLimit(env, ip) {
  let burst;
  let minute;
  try {
    [burst, minute] = await Promise.all([
      env.MCP_BURST.limit({ key: ip }),
      env.MCP_MINUTE.limit({ key: ip }),
    ]);
  } catch {
    return { unconfigured: true };
  }
  if (!burst || burst.success === false) {
    return { limited: true, limit: BURST_MAX, remaining: 0, reset: BURST_WINDOW_MS / 1000 };
  }
  if (!minute || minute.success === false) {
    return { limited: true, limit: MINUTE_MAX, remaining: 0, reset: MINUTE_WINDOW_MS / 1000 };
  }
  return { limited: false, limit: MINUTE_MAX, remaining: MINUTE_MAX, reset: MINUTE_WINDOW_MS / 1000 };
}

function rateHeaders(quota) {
  return {
    "X-RateLimit-Limit": String(quota.limit),
    "X-RateLimit-Remaining": String(quota.remaining),
    "Retry-After": String(quota.reset),
  };
}

function catSlug(name) {
  return String(name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function localityNote(loc) {
  if (loc === "offline") return "Listing says it can run on your own machine.";
  if (loc === "self_hosted") return "Listing says you can deploy it on your own server.";
  if (loc === "cloud") return "Listing describes a hosted service.";
  return "Not confirmed; check with the vendor.";
}

function passesLocality(tool, filter) {
  if (!filter || filter === "any") return true;
  if (filter === "offline") return tool.data_locality === "offline";
  if (filter === "self_hosted_or_offline") return tool.data_locality === "offline" || tool.data_locality === "self_hosted";
  return true;
}

function card(tool) {
  const loc = tool.data_locality || "unknown";
  return {
    name: tool.name,
    slug: tool.slug,
    category: tool.category,
    description: tool.description,
    pricing: tool.pricing,
    price_type: tool.price_tag || "unknown",
    open_source: !!tool.open_source,
    github_stars: tool.github_stars ?? null,
    website: tool.website || null,
    agentscout_url: tool.page || `https://agentscouthq.com/tools/${tool.slug}.html`,
    data_locality: loc,
    data_locality_note: localityNote(loc),
  };
}

function baseEnvelope(view) {
  return {
    source: "https://agentscouthq.com/",
    catalog_updated: view.updated,
    links_checked: view.last_checked,
    note: PRICE_NOTE,
    data_locality_caveat: LOCALITY_CAVEAT,
  };
}

function tokens(text) {
  return String(text || "").toLowerCase().split(/[^a-z0-9]+/).filter((part) => part.length >= 2);
}

function haystack(tool) {
  return [tool.name, tool.slug, tool.category, tool.description, ...(tool.tags || [])].join(" ").toLowerCase();
}

function matchTools(view, query, args, cap) {
  const words = tokens(query);
  const category = args.category ? String(args.category) : "";
  const pricing = args.pricing && args.pricing !== "any" ? String(args.pricing) : "";
  const openSource = args.open_source === true;
  const scored = [];
  for (const tool of view.tools) {
    if (category && tool.category !== category) continue;
    if (pricing && tool.price_tag !== pricing) continue;
    if (openSource && !tool.open_source) continue;
    if (!passesLocality(tool, args.runs_locally)) continue;
    const blob = haystack(tool);
    if (words.length && !words.every((word) => blob.includes(word))) continue;
    const name = String(tool.name || "").toLowerCase();
    const nameHits = words.reduce((n, word) => n + (name.includes(word) ? 1 : 0), 0);
    scored.push([nameHits, tool.github_stars || 0, tool]);
  }
  scored.sort((a, b) => b[0] - a[0] || b[1] - a[1] || String(a[2].name).localeCompare(String(b[2].name)));
  return { total: scored.length, rows: scored.slice(0, cap).map((row) => card(row[2])) };
}

function searchTools(view, args) {
  const query = args.query == null || args.query === "" ? "" : args.query;
  if (typeof query !== "string" || query.length > 200) return { error: "query must be a string of at most 200 characters." };
  const category = args.category == null || args.category === "" ? "" : args.category;
  if (typeof category !== "string" || category.length > 80) return { error: "category must be a string of at most 80 characters." };
  const limit = Math.min(25, Math.max(1, Number(args.limit) || 10));
  const found = matchTools(view, query, { ...args, category }, limit);
  return { ...baseEnvelope(view), total_matches: found.total, results: found.rows };
}

function bestForTask(view, args) {
  const task = args.task == null ? "" : args.task;
  if (typeof task !== "string" || task.length > 200) return { error: "task must be a string of at most 200 characters." };
  const category = args.category == null || args.category === "" ? "" : args.category;
  if (typeof category !== "string" || category.length > 80) return { error: "category must be a string of at most 80 characters." };
  const limit = Math.min(10, Math.max(1, Number(args.limit) || 5));
  const found = matchTools(view, task, { ...args, category }, limit);
  return { ...baseEnvelope(view), total_matches: found.total, results: found.rows };
}

function getTool(view, args) {
  const slug = String(args.slug || "");
  const tool = view.bySlug.get(slug);
  if (!tool) {
    return { error: `No AgentScout listing for slug '${slug}'.`, isError: true };
  }
  return {
    ...baseEnvelope(view),
    tool: {
      ...card(tool),
      key_features: tool.key_features || [],
      platforms: tool.platforms || [],
      tags: tool.tags || [],
      github: tool.github || null,
      license: tool.license || null,
      date_added: tool.date_added || null,
      data_locality_evidence: null,
    },
  };
}

function listCategories(view) {
  const counts = new Map();
  for (const tool of view.tools) {
    counts.set(tool.category, (counts.get(tool.category) || 0) + 1);
  }
  const categories = [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([name, count]) => ({
      name,
      tools: count,
      agentscout_url: `https://agentscouthq.com/categories/${catSlug(name)}.html`,
    }));
  return { ...baseEnvelope(view), total_tools: view.tools.length, categories };
}

function listPackages(args) {
  const filter = args.category || "all";
  const listing = (products.packages || []).map((item) => ({ ...item, group: "listing_package" }));
  const addons = (products.addons || []).map((item) => ({ ...item, group: "addon" }));
  const bots = (products.bot_templates || []).map((item) => ({ ...item, group: "bot_template" }));
  const packs = (products.agent_packs || []).map((item) => ({ ...item, group: "agent_pack" }));
  let rows = [...listing, ...addons, ...bots, ...packs];
  if (filter === "listing_package") rows = listing;
  else if (filter === "addon") rows = addons;
  else if (filter === "bot_template") rows = bots;
  else if (filter === "agent_pack") rows = packs;
  return {
    source: "https://agentscouthq.com/",
    catalog_updated: products.updated,
    note: PRICE_NOTE,
    protocol: "stripe-agentic-commerce-v1",
    products_feed_url: "https://agentscouthq.com/api/products.json",
    acp_manifest_url: "https://agentscouthq.com/.well-known/acp.json",
    pack_pricing: products.pack_pricing || null,
    pack_tier_urls: PACK_TIER_URLS,
    total_products: rows.length,
    products: rows,
  };
}

function toolResult(id, data, isError = false) {
  return {
    jsonrpc: "2.0",
    id,
    result: {
      content: [{ type: "text", text: JSON.stringify(data, null, 1) }],
      structuredContent: data,
      isError,
    },
  };
}

function rpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

function callTool(view, name, args) {
  const input = plainObject(args) ? args : {};
  if (name === "search_tools") {
    const data = searchTools(view, input);
    if (data.error) return { error: data.error };
    return { data };
  }
  if (name === "best_for_task") {
    if (typeof input.task !== "string" || input.task.trim().length < 2) {
      return { error: "task is required (at least 2 characters)." };
    }
    const data = bestForTask(view, input);
    if (data.error) return { error: data.error };
    return { data };
  }
  if (name === "get_tool") {
    if (!args || typeof args.slug !== "string" || !/^[a-z0-9][a-z0-9-]{0,99}$/.test(args.slug)) {
      return { error: "slug is required." };
    }
    const data = getTool(view, args);
    if (data.isError) return { data, isError: true };
    return { data };
  }
  if (name === "list_categories") return { data: listCategories(view) };
  if (name === "list_packages") return { data: listPackages(input) };
  if (typeof name !== "string" || name.length > 80 || /[\u0000-\u001f]/.test(name)) return { error: "Unknown tool." };
  return { error: `Unknown tool '${name}'.` };
}

function handleRpc(view, message) {
  const parsedId = rpcId(message);
  if (parsedId.error) return rpcError(null, -32600, "Invalid Request");
  const id = parsedId.id;
  const method = message.method;
  if (message.params != null && !plainObject(message.params)) return rpcError(id, -32600, "Invalid Request");
  const params = message.params || {};
  if (typeof method !== "string") return rpcError(id, -32600, "Invalid Request");
  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2025-06-18",
        capabilities: { tools: { listChanged: false } },
        serverInfo: SERVER_INFO,
        instructions: INSTRUCTIONS,
      },
    };
  }
  if (method === "ping") return { jsonrpc: "2.0", id, result: {} };
  if (method === "tools/list") return { jsonrpc: "2.0", id, result: { tools: TOOL_DEFS } };
  if (method === "tools/call") {
    const name = params.name;
    const called = callTool(view, name, params.arguments || {});
    if (called.error) return toolResult(id, { error: called.error }, true);
    return toolResult(id, called.data, !!called.isError);
  }
  if (method.startsWith("notifications/")) return null;
  if (method.length > MAX_METHOD || /[\u0000-\u001f]/.test(method)) return rpcError(id, -32601, "Method not found");
  return rpcError(id, -32601, `Method not found: ${method}`);
}

function registryBody() {
  return {
    servers: [
      {
        server: {
          $schema: "https://static.modelcontextprotocol.io/schemas/2025-09-29/server.schema.json",
          name: "com.agentscouthq/directory",
          title: "AgentScout Directory",
          description: "Read-only catalog of AI agents, app builders, and MCP servers, including Lovable and Lovable MCP.",
          version: "1.0.2",
          remotes: [
            { type: "streamable-http", url: "https://mcp.agentscouthq.com/mcp" },
          ],
        },
        _meta: {
          "io.modelcontextprotocol.registry/official": {
            status: "active",
            isLatest: true,
          },
        },
      },
    ],
    metadata: { count: 1, nextCursor: "" },
  };
}

function infoBody(view) {
  return {
    name: "AgentScout MCP server",
    endpoint: "https://mcp.agentscouthq.com/mcp",
    transport: "streamable-http",
    read_only: true,
    docs: "https://agentscouthq.com/mcp/connect.html",
    tools_indexed: view.count,
    categories: view.category_count,
    mcp_servers: view.mcp_count,
    catalog_updated: view.updated,
    links_checked: view.last_checked,
    tools: TOOL_DEFS.map((tool) => tool.name),
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const view = await loadCatalog();
    let status = 200;
    try {
      if (request.method === "OPTIONS") {
        status = 204;
        return emptyResponse(204);
      }
      if (!limitersReady(env)) {
        status = 503;
        console.error(JSON.stringify({ message: "rate limit binding missing", method: request.method, path: logToken(url.pathname), status }));
        return jsonResponse({ error: "Rate limiting is not configured." }, 503);
      }
      if (url.search.length > MAX_QUERY) {
        status = 400;
        return jsonResponse({ error: "Query too large" }, 400);
      }
      const ip = clientIp(request);
      if (!ip) {
        status = 403;
        return jsonResponse({ error: "Client address is unavailable." }, 403);
      }
      const quota = verifiedCrawler(request)
        ? { limited: false, limit: MINUTE_MAX, remaining: MINUTE_MAX, reset: 60 }
        : await rateLimit(env, ip);
      if (quota.unconfigured) {
        status = 503;
        console.error(JSON.stringify({ message: "rate limit binding failed", method: request.method, path: logToken(url.pathname), status }));
        return jsonResponse({ error: "Rate limiting is not configured." }, 503);
      }
      const extra = rateHeaders(quota);
      if (quota.limited) {
        status = 429;
        console.warn(JSON.stringify({ message: "rate limited", method: request.method, path: logToken(url.pathname), status }));
        return jsonResponse({ error: "Too many requests. Slow down and retry." }, 429, extra);
      }
      if (request.method === "GET" && url.pathname === "/v0/servers") {
        status = 200;
        console.log(JSON.stringify({ message: "mcp registry", method: "GET", path: logToken(url.pathname), status }));
        return jsonResponse(registryBody(), 200, extra);
      }
      if (request.method === "GET") {
        status = 200;
        console.log(JSON.stringify({ message: "mcp request", method: "GET", path: logToken(url.pathname), status }));
        return jsonResponse(infoBody(view), 200, extra);
      }
      if (request.method !== "POST") {
        status = 405;
        return jsonResponse({ error: "Method not allowed" }, 405, { ...extra, Allow: "GET, POST, OPTIONS" });
      }
      const read = await readCapped(request, MAX_BODY);
      if (read.error) {
        status = read.error === "too_large" ? 413 : 400;
        return jsonResponse(
          read.error === "too_large" ? { error: "Payload too large" } : rpcError(null, -32700, "Parse error"),
          status,
          extra,
        );
      }
      let message;
      try {
        message = JSON.parse(read.text || "{}");
      } catch {
        status = 400;
        return jsonResponse(rpcError(null, -32700, "Parse error"), 400, extra);
      }
      if (!plainObject(message)) {
        status = 400;
        return jsonResponse(rpcError(null, -32600, "Invalid Request"), 400, extra);
      }
      if (message && typeof message === "object" && message.method && String(message.method).startsWith("notifications/")) {
        status = 202;
        console.log(JSON.stringify({ message: "mcp notification", method: "POST", path: logToken(url.pathname), status }));
        return emptyResponse(202, extra);
      }
      const result = handleRpc(view, message);
      if (result == null) {
        status = 202;
        return emptyResponse(202, extra);
      }
      status = 200;
      console.log(JSON.stringify({ message: "mcp request", method: "POST", path: logToken(url.pathname), rpc: logToken(message.method), status }));
      return jsonResponse(result, 200, extra);
    } catch (error) {
      status = 500;
      console.error(JSON.stringify({
        message: "mcp request failed",
        method: request.method,
        path: logToken(url.pathname),
        status,
        error: logToken(error instanceof Error ? error.message : "error"),
      }));
      return jsonResponse({ error: "Internal server error" }, 500);
    }
  },
};
