/**
 * AgentScout vote + roast API.
 * Hostname: https://votes.agentscouthq.com (custom domain on this worker).
 * Do not route these paths on api.agentscouthq.com; that host belongs to agentscout-image.
 *
 * Binding: VOTES (KV). One key per ISO week, votes:2026-w44 -> { day, week: {slug: count}, today: {slug: count} }.
 * GET /votes reads that key once. POST /vote checks a per-visitor seen key, then read-modify-writes the week document.
 * Two votes that land together can drop a count (last write wins). That race is a known pilot limitation.
 */
import { isBlockedIp, validateUrlShape, resolveAndCheck } from "./ssrf.js";
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
      "content-type": "application/json; charset=utf-8",
      "cache-control": cache,
      ...corsHeaders(request),
    },
  });
}

function clientIp(request) {
  return request.headers.get("cf-connecting-ip")
    || (request.headers.get("x-forwarded-for") || "").split(",")[0].trim()
    || "0.0.0.0";
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

async function rateLimit(env, bucket, ip, limit) {
  const key = `rl:${bucket}:${ip}:${Math.floor(Date.now() / 60000)}`;
  if (env.VOTES) {
    const cur = Number(await env.VOTES.get(key)) || 0;
    if (cur >= limit) return false;
    await env.VOTES.put(key, String(cur + 1), { expirationTtl: 120 });
    return true;
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
  if (!env.VOTES) return `memory-${day}`;
  let salt = await env.VOTES.get(key);
  if (!salt) {
    salt = crypto.randomUUID();
    await env.VOTES.put(key, salt, { expirationTtl: 60 * 60 * 72 });
    salt = (await env.VOTES.get(key)) || salt;
  }
  return salt;
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

async function fetchPublic(target, depth = 0) {
  const shape = validateUrlShape(target);
  if (shape.error) return shape;
  const dns = await resolveAndCheck(shape.url.hostname);
  if (dns.error) return dns;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), FETCH_MS);
  let response;
  try {
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

async function catalogMatch(finalHost) {
  const res = await fetch("https://agentscouthq.com/api/tools.json", { cf: { cacheTtl: 3600 } });
  if (!res.ok) return null;
  const data = await res.json();
  const tools = Array.isArray(data) ? data : data.tools || [];
  const host = finalHost.replace(/^www\./, "");
  for (const tool of tools) {
    for (const field of ["website", "url"]) {
      try {
        const h = new URL(tool[field]).hostname.replace(/^www\./, "").toLowerCase();
        if (h && h === host) {
          return { slug: tool.slug, name: tool.name, page: `https://agentscouthq.com/tools/${tool.slug}.html` };
        }
      } catch { /* skip bad urls */ }
    }
  }
  return null;
}

async function roast(request, env) {
  if (!(await rateLimit(env, "roast", clientIp(request), ROAST_PER_MIN))) return json(request, { error: "Too many checks. Try again in a minute." }, 429);
  const url = new URL(request.url);
  let target = url.searchParams.get("url") || "";
  if (request.method === "POST") {
    const body = await request.json().catch(() => ({}));
    target = body.url || target;
  }
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

async function vote(request, env) {
  if (!voteAllowed(request)) return json(request, { error: "Votes can only be cast from agentscouthq.com." }, 403);
  if (!env.VOTES) return json(request, { error: "Vote storage is not configured." }, 503);
  if (!(await rateLimit(env, "vote", clientIp(request), VOTE_PER_MIN))) return json(request, { error: "Too many votes. Try again in a minute." }, 429);
  const body = await request.json().catch(() => ({}));
  const slug = String(body.slug || "");
  if (!SLUG_RE.test(slug)) return json(request, { error: "Unknown tool." }, 400);
  const day = ptDay();
  const week = isoWeek(day);
  const salt = await dailySalt(env, day);
  const visitor = await sha256(`${salt}\n${clientIp(request)}\n${slug}`);
  const seenKey = `seen:${day}:${visitor}`;
  const already = await env.VOTES.get(seenKey);
  const key = `votes:${week}`;
  const stored = normalizeStored(await env.VOTES.get(key, "json"), day);
  const doc = already ? stored : castInDoc(stored, slug, day);
  if (!already) {
    await env.VOTES.put(seenKey, "1", { expirationTtl: 60 * 60 * 48 });
    await env.VOTES.put(key, JSON.stringify({ day: doc.day, week: doc.week, today: doc.today }));
  }
  return json(request, {
    ok: true,
    slug,
    week,
    votes: Number(doc.week[slug]) || 0,
    today: Number(doc.today[slug]) || 0,
    already: !!already,
    yours: true,
  });
}

async function votes(request, env) {
  const url = new URL(request.url);
  const slugs = parseSlugs(url.searchParams.get("slugs"));
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
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(request) });
    const path = new URL(request.url).pathname.replace(/\/$/, "") || "/";
    try {
      if (path === "/roast" && (request.method === "GET" || request.method === "POST")) return await roast(request, env);
      if (path === "/vote" && request.method === "POST") return await vote(request, env);
      if (path === "/votes" && request.method === "GET") return await votes(request, env);
      return json(request, { error: "Not found", endpoints: ["/roast", "/vote", "/votes"] }, 404);
    } catch (err) {
      return json(request, { error: "The check failed. Try again in a minute." }, 500);
    }
  },
};

export { isBlockedIp, ptDay, isoWeek };
