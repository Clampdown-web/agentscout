/**
 * AgentScout vote + roast API.
 * Hostname: https://votes.agentscouthq.com (custom domain on this worker).
 * Do not route these paths on api.agentscouthq.com; that host belongs to agentscout-image.
 *
 * Binding: VOTES (KV). One key per ISO week, votes:2026-w44 -> { day, week: {slug: count}, today: {slug: count} }.
 * GET /votes reads that key once. POST /vote creates the per-visitor seen key only if it is absent, then read-modify-writes the week document.
 * Two votes that land together can still drop a count on the week document (last write wins). That race is a known pilot limitation.
 */
import { isBlockedIp, isIpLiteral, validateUrlShape, resolveAndCheck } from "./ssrf.js";
import { scoreListing } from "./score.js";

const ALLOWED_ORIGINS = new Set([
  "https://agentscouthq.com",
  "https://www.agentscouthq.com",
]);
const MAX_BYTES = 512_000;
const FETCH_MS = 8_000;
const MAX_REDIRECTS = 3;
const ROAST_PER_MIN = 8;
const VOTE_PER_MIN = 30;
const MAX_SLUGS = 400;
const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,80}$/;
const MAX_JSON_BODY = 16_384;
const MAX_URL_PARAM = 4_096;
const MAX_SLUGS_PARAM = 40_000;
// The live directory (api/tools.json) is larger than 6MB. A lower cap made
// catalogMatch give up before JSON.parse, or copy most of the file and still
// miss. 16MB leaves room past the current ~7MB catalog. The host index below
// is what a request keeps, not the parsed file.
const MAX_CATALOG_BYTES = 16_000_000;
const CATALOG_URL = "https://agentscouthq.com/api/tools.json";
// Edge fetch cache and the per-isolate index use the same lifetime.
export const CATALOG_CACHE_TTL_SECONDS = 3600;
const CATALOG_TTL_MS = CATALOG_CACHE_TTL_SECONDS * 1000;
const MAX_IP_LEN = 128;

const SECURITY_HEADERS = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "strict-origin-when-cross-origin",
  "strict-transport-security": "max-age=31536000; includeSubDomains",
  "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
};

const memoryBuckets = new Map();

export function allowOrigin(origin) {
  return ALLOWED_ORIGINS.has(origin) ? origin : "";
}

export function voteAllowed(request) {
  const origin = request.headers.get("Origin") || request.headers.get("origin") || "";
  if (origin) return ALLOWED_ORIGINS.has(origin);
  const referer = request.headers.get("Referer") || request.headers.get("referer") || "";
  if (!referer) return false;
  try {
    return ALLOWED_ORIGINS.has(new URL(referer).origin);
  } catch {
    return false;
  }
}

export function corsHeaders(request) {
  const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
  const headers = {
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
    vary: "Origin",
  };
  if (origin) headers["access-control-allow-origin"] = origin;
  return headers;
}

function json(request, body, status = 200, cache = "no-store") {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...SECURITY_HEADERS,
      "content-type": "application/json; charset=utf-8",
      "cache-control": cache,
      ...corsHeaders(request),
    },
  });
}

function clientIp(request) {
  const ip = (request.headers.get("cf-connecting-ip") || "").trim();
  if (!ip || ip.length > MAX_IP_LEN || /[\u0000-\u0020]/.test(ip)) return "";
  return ip;
}

async function readCapped(response, max) {
  const declared = Number(response.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > max) return { error: "too_large" };
  const reader = response.body?.getReader?.();
  if (!reader) {
    const text = typeof response.text === "function" ? await response.text() : "";
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

function parseObject(text) {
  if (!text) return {};
  try {
    const value = JSON.parse(text);
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return value;
  } catch {
    return {};
  }
}

function ptDay(now = new Date()) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

function isoWeek(day) {
  const [y, m, d] = day.split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  const dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
  return `${date.getUTCFullYear()}-w${String(week).padStart(2, "0")}`;
}

export function parseSlugs(raw) {
  return [...new Set(String(raw || "").split(",").map((s) => s.trim()).filter((s) => SLUG_RE.test(s)))].slice(0, MAX_SLUGS);
}

export function normalizeStored(raw, day) {
  const src = raw && typeof raw === "object" ? raw : {};
  const week = {};
  if (src.week && typeof src.week === "object") {
    for (const [k, v] of Object.entries(src.week)) {
      if (SLUG_RE.test(k)) week[k] = Number(v) || 0;
    }
  }
  const sameDay = src.day === day;
  const today = {};
  if (sameDay && src.today && typeof src.today === "object") {
    for (const [k, v] of Object.entries(src.today)) {
      if (SLUG_RE.test(k)) today[k] = Number(v) || 0;
    }
  }
  return { day: sameDay ? day : "", week, today };
}

export function castInDoc(doc, slug, day) {
  const next = {
    day,
    week: { ...doc.week },
    today: doc.day === day ? { ...doc.today } : {},
  };
  next.week[slug] = (Number(next.week[slug]) || 0) + 1;
  next.today[slug] = (Number(next.today[slug]) || 0) + 1;
  return next;
}

export function countsFor(doc, slugs, day) {
  const tools = {};
  let todayTotal = 0;
  const useToday = doc.day === day;
  for (const slug of slugs) {
    const votes = Number(doc.week[slug]) || 0;
    const today = useToday ? (Number(doc.today[slug]) || 0) : 0;
    tools[slug] = { votes, today };
    todayTotal += today;
  }
  return { tools, today_total: todayTotal };
}

// ROAST_RL / VOTE_RL are the Workers Rate Limiting bindings from wrangler.toml.
// limit() is keyed by the client IP (CF-Connecting-IP), not X-Forwarded-For.
// When the binding exists it is the only counter: success must be true, and a
// throw fails closed. The KV and in-memory fallbacks below do not run.
// The binding is per Cloudflare location and eventually consistent, so a short
// burst can overshoot the configured limit slightly. It is not one worldwide
// counter. The fallback is only for an isolate started without the binding,
// and that fallback is still one isolate.
function rateBinding(env, bucket) {
  if (!env) return null;
  if (bucket === "roast") return env.ROAST_RL;
  if (bucket === "vote") return env.VOTE_RL;
  return null;
}

async function rateLimit(env, bucket, ip, limit) {
  const binding = rateBinding(env, bucket);
  if (binding && typeof binding.limit === "function") {
    try {
      const result = await binding.limit({ key: ip });
      return !!(result && result.success === true);
    } catch {
      return false;
    }
  }
  const key = `rl:${bucket}:${ip}:${Math.floor(Date.now() / 60000)}`;
  if (env.VOTES) {
    return withSeenLock(key, async () => {
      const cur = Number(await env.VOTES.get(key)) || 0;
      if (cur >= limit) return false;
      await env.VOTES.put(key, String(cur + 1), { expirationTtl: 120 });
      return true;
    });
  }
  const cur = memoryBuckets.get(key) || 0;
  if (cur >= limit) return false;
  memoryBuckets.set(key, cur + 1);
  return true;
}

async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function dailySalt(env, day) {
  const key = `salt:${day}`;
  if (!env.VOTES) return "";
  return withSeenLock(key, async () => {
    let salt = await env.VOTES.get(key);
    if (typeof salt === "string" && salt) return salt;
    try {
      await env.VOTES.put(key, crypto.randomUUID(), { expirationTtl: 60 * 60 * 72 });
    } catch (err) {
      if (!kvConflict(err)) throw err;
    }
    salt = await env.VOTES.get(key);
    return typeof salt === "string" && salt ? salt : "";
  });
}

const seenLocks = new Map();

function withSeenLock(key, fn) {
  const prev = seenLocks.get(key) || Promise.resolve();
  const run = prev.then(() => fn(), () => fn());
  const settled = run.then(() => {}, () => {});
  seenLocks.set(key, settled);
  settled.then(() => { if (seenLocks.get(key) === settled) seenLocks.delete(key); });
  return run;
}

function kvConflict(err) {
  const msg = String((err && err.message) || err || "");
  return msg.includes("429") || msg.toLowerCase().includes("too many requests");
}

async function claimSeen(kv, key) {
  const claim = crypto.randomUUID();
  const opts = { expirationTtl: 60 * 60 * 48 };
  if (typeof kv.putIfAbsent === "function") return (await kv.putIfAbsent(key, claim, opts)) === true;
  const existing = await kv.get(key);
  if (existing) return false;
  try {
    await kv.put(key, claim, opts);
  } catch (err) {
    if (kvConflict(err)) return false;
    throw err;
  }
  return (await kv.get(key)) === claim;
}

async function readLimited(response) {
  const reader = response.body?.getReader();
  if (!reader) return { error: "That page had nothing to score." };
  const chunks = [];
  let size = 0;
  try {
    while (size < MAX_BYTES) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value?.byteLength) continue;
      const room = MAX_BYTES - size;
      if (value.byteLength > room) {
        chunks.push(value.subarray(0, room));
        size += room;
        break;
      }
      chunks.push(value);
      size += value.byteLength;
    }
  } catch (err) {
    if (!size) throw err;
  } finally {
    try { await reader.cancel(); } catch { /* already closed */ }
  }
  if (!size) return { error: "That page had nothing to score." };
  const buf = new Uint8Array(size);
  let off = 0;
  for (const chunk of chunks) { buf.set(chunk, off); off += chunk.byteLength; }
  const text = new TextDecoder("utf-8", { fatal: false }).decode(buf);
  if (!text.trim()) return { error: "That page had nothing to score." };
  return { text };
}

function sameIp(a, b) {
  const norm = (ip) => String(ip || "").trim().toLowerCase().replace(/^\[|\]$/g, "").split("%")[0];
  return norm(a) === norm(b);
}

function acceptedAddresses(addresses) {
  const out = [];
  for (const raw of addresses || []) {
    const ip = String(raw || "").trim().replace(/\.$/, "");
    if (!isIpLiteral(ip) || isBlockedIp(ip)) continue;
    if (!out.some((have) => sameIp(have, ip))) out.push(ip);
  }
  return out;
}

function reportedPeer(response) {
  if (!response || typeof response !== "object") return "";
  if (typeof response.peerAddress === "string" && response.peerAddress.trim()) return response.peerAddress.trim();
  const cf = response.cf;
  if (cf && typeof cf === "object") {
    for (const key of ["resolvedIp", "originIp"]) {
      if (typeof cf[key] === "string" && cf[key].trim()) return cf[key].trim();
    }
  }
  return "";
}

async function fetchPublic(target, depth = 0) {
  const shape = validateUrlShape(target);
  if (shape.error) return shape;
  const dns = await resolveAndCheck(shape.url.hostname);
  if (dns.error) return dns;
  const allowed = acceptedAddresses(dns.addresses);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), FETCH_MS);
  let response;
  try {
    // Fetch the hostname. Workers cannot dial an arbitrary checked address and
    // still validate TLS. Public egress does not route to private or link-local
    // ranges. redirect:manual so every hop runs this check again.
    response = await fetch(shape.url.toString(), {
      redirect: "manual",
      signal: ctrl.signal,
      headers: { "user-agent": "AgentScoutRoast/1.0 (+https://agentscouthq.com/free-tools/roast-my-ai-tool-listing.html)" },
    });
  } catch {
    return { error: "The site did not respond in time." };
  } finally {
    clearTimeout(timer);
  }
  const peer = reportedPeer(response);
  if (peer && !allowed.some((ip) => sameIp(ip, peer))) {
    try { await response.body?.cancel(); } catch { /* already closed */ }
    return { error: "That host resolves to a blocked address." };
  }
  if (response.status >= 300 && response.status < 400) {
    if (depth >= MAX_REDIRECTS) return { error: "Too many redirects." };
    const loc = response.headers.get("location");
    if (!loc) return { error: "Redirect had no destination." };
    const next = new URL(loc, shape.url).toString();
    return fetchPublic(next, depth + 1);
  }
  const body = await readLimited(response);
  if (body.error) return body;
  return { url: shape.url, status: response.status, text: body.text, addresses: dns.addresses };
}

let catalogCache = null;
let catalogPending = null;
let catalogEpoch = 0;

function hostFromUrl(value) {
  try {
    return new URL(value).hostname.replace(/^www\./, "").toLowerCase();
  } catch {
    return "";
  }
}

function indexCatalog(data) {
  const tools = Array.isArray(data) ? data : (data && data.tools) || [];
  const byHost = new Map();
  for (const tool of tools) {
    if (!tool || typeof tool !== "object" || typeof tool.slug !== "string" || !tool.slug) continue;
    const entry = {
      slug: tool.slug,
      name: tool.name,
      page: `https://agentscouthq.com/tools/${tool.slug}.html`,
    };
    for (const field of ["website", "url"]) {
      const host = hostFromUrl(tool[field]);
      if (host && !byHost.has(host)) byHost.set(host, entry);
    }
  }
  return byHost;
}

async function fetchCatalogIndex() {
  const epoch = catalogEpoch;
  const res = await fetch(CATALOG_URL, {
    cf: { cacheTtl: CATALOG_CACHE_TTL_SECONDS, cacheEverything: true },
  });
  if (!res.ok) return catalogCache ? catalogCache.byHost : null;
  // A known length under the cap can be decoded once. Chunked bodies still
  // stop at the cap, so a huge response is not parsed.
  const declared = Number(res.headers.get("content-length"));
  let text = "";
  if (Number.isFinite(declared)) {
    if (declared > MAX_CATALOG_BYTES) {
      try { await res.body?.cancel(); } catch { /* already closed */ }
      return catalogCache ? catalogCache.byHost : null;
    }
    text = typeof res.text === "function" ? await res.text() : "";
    if (text.length > MAX_CATALOG_BYTES) return catalogCache ? catalogCache.byHost : null;
  } else {
    const body = await readCapped(res, MAX_CATALOG_BYTES);
    if (body.error || !body.text) return catalogCache ? catalogCache.byHost : null;
    text = body.text;
  }
  const data = JSON.parse(text);
  const byHost = indexCatalog(data);
  if (epoch !== catalogEpoch) return byHost;
  catalogCache = { at: Date.now(), byHost };
  return byHost;
}

async function catalogIndex() {
  const now = Date.now();
  if (catalogCache && now - catalogCache.at < CATALOG_TTL_MS) return catalogCache.byHost;
  if (!catalogPending) {
    const pending = fetchCatalogIndex();
    catalogPending = pending;
    pending.finally(() => {
      if (catalogPending === pending) catalogPending = null;
    }).catch(() => {});
  }
  return catalogPending;
}

// One host index per isolate. Parallel /roast calls share the in-flight
// fetch, and later calls skip the download and JSON.parse until the TTL.
async function catalogMatch(finalHost) {
  const byHost = await catalogIndex();
  if (!byHost) return null;
  const host = String(finalHost || "").toLowerCase().replace(/^www\./, "");
  if (!host) return null;
  return byHost.get(host) || null;
}

export function resetCatalogCache() {
  catalogEpoch += 1;
  catalogCache = null;
  catalogPending = null;
}

export function expireCatalogCache() {
  if (catalogCache) catalogCache.at = 0;
}

async function roast(request, env) {
  if (!env.VOTES) return json(request, { error: "Vote storage is not configured." }, 503);
  const ip = clientIp(request);
  if (!ip) return json(request, { error: "Client address is unavailable." }, 403);
  if (request.method === "POST") {
    const declared = Number(request.headers.get("content-length"));
    if (Number.isFinite(declared) && declared > MAX_JSON_BODY) return json(request, { error: "Payload too large." }, 413);
  }
  // Reject a flood before the body, DNS, the page fetch, or the catalog index.
  if (!(await rateLimit(env, "roast", ip, ROAST_PER_MIN))) return json(request, { error: "Too many checks. Try again in a minute." }, 429);
  const url = new URL(request.url);
  let target = url.searchParams.get("url") || "";
  if (request.method === "POST") {
    const body = await readCapped(request, MAX_JSON_BODY);
    if (body.error === "too_large") return json(request, { error: "Payload too large." }, 413);
    if (body.error) return json(request, { error: "The check failed. Try again in a minute." }, 400);
    const parsed = parseObject(body.text);
    target = (typeof parsed.url === "string" ? parsed.url : "") || target;
  }
  if (target.length > MAX_URL_PARAM) return json(request, { error: "Enter a public http or https URL." }, 400);
  const page = await fetchPublic(target);
  if (page.error) return json(request, { error: page.error }, 400);
  const origin = page.url.origin;
  const llms = await fetchPublic(origin + "/llms.txt");
  const listed = await catalogMatch(page.url.hostname);
  const score = scoreListing({
    html: page.text,
    llmsStatus: llms.status || 0,
    llmsText: llms.text || "",
    listed,
  });
  return json(request, { ok: true, final_url: page.url.toString(), ...score });
}

async function castVote(env, seenKey, slug, day, week) {
  const won = await claimSeen(env.VOTES, seenKey);
  const key = `votes:${week}`;
  const stored = normalizeStored(await env.VOTES.get(key, "json"), day);
  const doc = won ? castInDoc(stored, slug, day) : stored;
  if (won) await env.VOTES.put(key, JSON.stringify({ day: doc.day, week: doc.week, today: doc.today }));
  return {
    ok: true,
    slug,
    week,
    votes: Number(doc.week[slug]) || 0,
    today: Number(doc.today[slug]) || 0,
    already: !won,
    yours: true,
  };
}

async function vote(request, env) {
  if (!voteAllowed(request)) return json(request, { error: "Votes can only be cast from agentscouthq.com." }, 403);
  if (!env.VOTES) return json(request, { error: "Vote storage is not configured." }, 503);
  const ip = clientIp(request);
  if (!ip) return json(request, { error: "Client address is unavailable." }, 403);
  const declared = Number(request.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > MAX_JSON_BODY) return json(request, { error: "Payload too large." }, 413);
  if (!(await rateLimit(env, "vote", ip, VOTE_PER_MIN))) return json(request, { error: "Too many votes. Try again in a minute." }, 429);
  const raw = await readCapped(request, MAX_JSON_BODY);
  if (raw.error === "too_large") return json(request, { error: "Payload too large." }, 413);
  if (raw.error) return json(request, { error: "The check failed. Try again in a minute." }, 400);
  const body = parseObject(raw.text);
  const slug = typeof body.slug === "string" ? body.slug : "";
  if (!SLUG_RE.test(slug)) return json(request, { error: "Unknown tool." }, 400);
  const day = ptDay();
  const week = isoWeek(day);
  const salt = await dailySalt(env, day);
  if (!salt) return json(request, { error: "Vote storage is not ready." }, 503);
  const visitor = await sha256(`${salt}\n${ip}\n${slug}`);
  const seenKey = `seen:${day}:${visitor}`;
  const result = await withSeenLock(seenKey, () => castVote(env, seenKey, slug, day, week));
  return json(request, result);
}

async function votes(request, env) {
  const url = new URL(request.url);
  const rawSlugs = url.searchParams.get("slugs") || "";
  if (rawSlugs.length > MAX_SLUGS_PARAM) return json(request, { error: "Too many tools." }, 400);
  const slugs = parseSlugs(rawSlugs);
  const day = ptDay();
  const week = isoWeek(day);
  if (!env.VOTES) {
    const empty = countsFor({ day: "", week: {}, today: {} }, slugs, day);
    return json(request, { ok: true, week, day, ...empty, storage: "unconfigured" });
  }
  const doc = normalizeStored(await env.VOTES.get(`votes:${week}`, "json"), day);
  const counts = countsFor(doc, slugs, day);
  return json(request, { ok: true, week, day, ...counts }, 200, "public, max-age=60");
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: { ...SECURITY_HEADERS, ...corsHeaders(request) } });
    }
    const path = new URL(request.url).pathname.replace(/\/$/, "") || "/";
    try {
      if (path === "/roast" && (request.method === "GET" || request.method === "POST")) return await roast(request, env);
      if (path === "/vote" && request.method === "POST") return await vote(request, env);
      if (path === "/votes" && request.method === "GET") return await votes(request, env);
      return json(request, { error: "Not found", endpoints: ["/roast", "/vote", "/votes"] }, 404);
    } catch {
      console.error(JSON.stringify({
        message: "vote request failed",
        path,
        status: 500,
      }));
      return json(request, { error: "The check failed. Try again in a minute." }, 500);
    }
  },
};

export { isBlockedIp, ptDay, isoWeek, MAX_CATALOG_BYTES };
