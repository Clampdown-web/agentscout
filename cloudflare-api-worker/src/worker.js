/**
 * AgentScout API routes for /roast, /vote, and /votes.
 * Deploy beside the existing api.agentscouthq.com worker on these paths only.
 * Do not replace the whole hostname: submit, generate, reviews, and track stay on the current worker.
 *
 * Binding: VOTES (KV). Create with `npx wrangler kv namespace create VOTES` and paste the id into wrangler.toml.
 */
import { isBlockedIp, validateUrlShape, resolveAndCheck } from "./ssrf.js";
import { scoreListing } from "./score.js";

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type",
  "access-control-max-age": "86400",
};
const MAX_BYTES = 512_000;
const FETCH_MS = 8_000;
const MAX_REDIRECTS = 3;
const ROAST_PER_MIN = 8;
const VOTE_PER_MIN = 30;

const memoryBuckets = new Map();

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...CORS },
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
  const len = Number(response.headers.get("content-length") || 0);
  if (len > MAX_BYTES) return { error: "That page is too large to score." };
  const reader = response.body?.getReader();
  if (!reader) return { text: "" };
  const chunks = [];
  let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > MAX_BYTES) {
      await reader.cancel();
      return { error: "That page is too large to score." };
    }
    chunks.push(value);
  }
  const buf = new Uint8Array(size);
  let off = 0;
  for (const chunk of chunks) { buf.set(chunk, off); off += chunk.byteLength; }
  return { text: new TextDecoder("utf-8", { fatal: false }).decode(buf) };
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
  if (!(await rateLimit(env, "roast", clientIp(request), ROAST_PER_MIN))) return json({ error: "Too many checks. Try again in a minute." }, 429);
  const url = new URL(request.url);
  let target = url.searchParams.get("url") || "";
  if (request.method === "POST") {
    const body = await request.json().catch(() => ({}));
    target = body.url || target;
  }
  const page = await fetchPublic(target);
  if (page.error) return json({ error: page.error }, 400);
  const origin = page.url.origin;
  const llms = await fetchPublic(origin + "/llms.txt");
  const listed = await catalogMatch(page.url.hostname);
  const score = scoreListing({
    html: page.text,
    llmsStatus: llms.status || 0,
    llmsText: llms.text || "",
    listed,
  });
  return json({ ok: true, final_url: page.url.toString(), ...score });
}

async function vote(request, env) {
  if (!env.VOTES) return json({ error: "Vote storage is not configured." }, 503);
  if (!(await rateLimit(env, "vote", clientIp(request), VOTE_PER_MIN))) return json({ error: "Too many votes. Try again in a minute." }, 429);
  const body = await request.json().catch(() => ({}));
  const slug = String(body.slug || "");
  if (!/^[a-z0-9][a-z0-9-]{0,80}$/.test(slug)) return json({ error: "Unknown tool." }, 400);
  const day = ptDay();
  const week = isoWeek(day);
  const salt = await dailySalt(env, day);
  const visitor = await sha256(`${salt}\n${clientIp(request)}\n${slug}`);
  const seenKey = `seen:${day}:${visitor}`;
  const weekKey = `week:${week}:${slug}`;
  const dayKey = `day:${day}:${slug}`;
  const already = await env.VOTES.get(seenKey);
  let votes = Number(await env.VOTES.get(weekKey)) || 0;
  let today = Number(await env.VOTES.get(dayKey)) || 0;
  if (!already) {
    votes += 1;
    today += 1;
    await env.VOTES.put(seenKey, "1", { expirationTtl: 60 * 60 * 48 });
    await env.VOTES.put(weekKey, String(votes));
    await env.VOTES.put(dayKey, String(today), { expirationTtl: 60 * 60 * 72 });
  }
  return json({ ok: true, slug, week, votes, today, already: !!already, voted: true });
}

async function votes(request, env) {
  const url = new URL(request.url);
  const slugs = [...new Set((url.searchParams.get("slugs") || "").split(",").map((s) => s.trim()).filter((s) => /^[a-z0-9][a-z0-9-]{0,80}$/.test(s)))].slice(0, 400);
  const day = ptDay();
  const week = isoWeek(day);
  const tools = {};
  let todayTotal = 0;
  if (!env.VOTES) {
    slugs.forEach((slug) => { tools[slug] = { votes: 0, today: 0, yours: false }; });
    return json({ ok: true, week, day, tools, today_total: 0, storage: "unconfigured" });
  }
  const salt = await dailySalt(env, day);
  const ip = clientIp(request);
  await Promise.all(slugs.map(async (slug) => {
    const votesN = Number(await env.VOTES.get(`week:${week}:${slug}`)) || 0;
    const today = Number(await env.VOTES.get(`day:${day}:${slug}`)) || 0;
    const visitor = await sha256(`${salt}\n${ip}\n${slug}`);
    const yours = !!(await env.VOTES.get(`seen:${day}:${visitor}`));
    tools[slug] = { votes: votesN, today, yours };
    todayTotal += today;
  }));
  return json({ ok: true, week, day, tools, today_total: todayTotal });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    const path = new URL(request.url).pathname.replace(/\/$/, "") || "/";
    try {
      if (path === "/roast" && (request.method === "GET" || request.method === "POST")) return await roast(request, env);
      if (path === "/vote" && request.method === "POST") return await vote(request, env);
      if (path === "/votes" && request.method === "GET") return await votes(request, env);
      return json({ error: "Not found", endpoints: ["/roast", "/vote", "/votes"] }, 404);
    } catch (err) {
      return json({ error: "The check failed. Try again in a minute." }, 500);
    }
  },
};

export { isBlockedIp, ptDay, isoWeek };
