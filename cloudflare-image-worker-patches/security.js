/**
 * Drop-in guard for the agentscout-image worker (api.agentscouthq.com).
 * The worker source is not in this repo. Wrap its export with protect().
 *
 * Guards /submit, /review, and /reviews (the review form posts to /review).
 * POST /generate gets the same origin allowlist and IMAGE_WRITE limit as
 * POST /submit, including when TURNSTILE_ENABLED is unset. GET /generate,
 * /track, /geo, and /share are otherwise unchanged. GET /readiness is
 * forwarded only after its url query passes validateUrlShape and resolveAndCheck.
 * A blocked address, a blocked DNS answer, a lookup failure, or a url longer
 * than 4096 characters is 400. GET /readiness counts against IMAGE_READ when
 * that binding exists; a missing binding leaves the request uncapped.
 * POST /review and POST /reviews bodies are capped at 32 KiB. POST /track and
 * POST /share bodies are capped at 64 KiB. POST /submit and POST /generate
 * keep the Turnstile body handling. JSON responses from this wrapper set
 * nosniff, frame deny, referrer policy, HSTS, and a default-src none policy.
 * /stats and /trending/stats drop a reflected allow-origin of *.
 *
 * When env.TURNSTILE_ENABLED === "true", POST /submit and POST /generate
 * are siteverify'd (secret, token, remoteip = CF-Connecting-IP) before the
 * inner handler runs. Failure or a hostname outside the site allowlist is 403.
 * POST /submit also requires the widget action "submit". POST /generate does
 * not: generate.js does not send an action, and requiring one here would
 * reject every generation until that page changes. A missing CF-Connecting-IP
 * fails closed. Deploy must set that plain-text var to true or the check stays off.
 *
 * X-Stats-Key on /reviews/pending, /reviews/admin, /reviews/export, /stats,
 * and /trending/stats is compared with safeEq (SHA-256, then a constant-time
 * compare) before the inner handler runs. A mismatch is 403. /reviews/export
 * is served here and is not cached and has no CORS allow-origin header. It is
 * not on the captured running script until that script is deployed.
 *
 * Bindings (Workers Rate Limiting, per CF-Connecting-IP):
 *   IMAGE_WRITE  10 requests / 60s   POST and other non-read methods
 *   IMAGE_READ  120 requests / 60s   GET and HEAD
 * A missing binding fails closed with 503. There is no User-Agent bypass.
 */
import { resolveAndCheck, validateUrlShape } from "../cloudflare-api-worker/src/ssrf.js";
import { EXPORT_PATH, exportEnabled, handleReviewsExport } from "./reviews-backup.js";

const SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const ALLOWED_HOSTS = new Set([
  "agentscouthq.com",
  "www.agentscouthq.com",
]);
const STATS_KEY_PATHS = new Set([
  "/reviews/pending",
  "/reviews/admin",
  "/reviews/export",
  "/stats",
  "/trending/stats",
]);
const TURNSTILE_PATHS = new Set(["/submit", "/generate"]);
const SUBMIT_ACTION = "submit";
const MAX_TURNSTILE_BODY = 100_000;
const MAX_TURNSTILE_TOKEN = 2048;
const MAX_REVIEW_BODY = 32_768;
const MAX_TRACK_BODY = 65_536;
const MAX_READY_URL = 4_096;
const TURNSTILE_RETRY_ERROR = "The check expired or was already used. Complete it again, then submit.";
const TURNSTILE_STALE_PAGE = "This page needs a fresh check. Reload it, complete the check again, then submit.";

const SECURITY_HEADERS = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "strict-origin-when-cross-origin",
  "strict-transport-security": "max-age=31536000; includeSubDomains",
  "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
};
const ALLOWED_ORIGINS = new Set([
  "https://agentscouthq.com",
  "https://www.agentscouthq.com",
]);

export function allowOrigin(origin) {
  return ALLOWED_ORIGINS.has(origin) ? origin : "";
}

export function postAllowed(request) {
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

export function normalizePath(pathname) {
  return String(pathname || "/").replace(/\/+$/, "") || "/";
}

export function guardedKind(pathname) {
  const path = normalizePath(pathname);
  if (path === "/submit") return "submit";
  if (path === "/generate") return "generate";
  if (path === "/review" || path === "/reviews" || path.startsWith("/reviews/")) return "reviews";
  return "";
}

function requestGuarded(pathname, method) {
  const kind = guardedKind(pathname);
  if (kind === "generate" && method !== "POST" && method !== "OPTIONS") return "";
  return kind;
}

export function statsKeyPath(pathname) {
  return STATS_KEY_PATHS.has(normalizePath(pathname));
}

export function turnstileEnabled(env) {
  return String((env && env.TURNSTILE_ENABLED) || "") === "true";
}

/**
 * Constant-time secret compare. Both sides are hashed to 32 bytes first so a
 * length mismatch cannot bail out early. Workers use crypto.subtle.timingSafeEqual;
 * other runtimes fall back to a full-length XOR of those hashes.
 */
export async function safeEq(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || !a || !b) return false;
  const encoder = new TextEncoder();
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(a)),
    crypto.subtle.digest("SHA-256", encoder.encode(b)),
  ]);
  const left = new Uint8Array(providedHash);
  const right = new Uint8Array(expectedHash);
  const timingSafeEqual = crypto.subtle.timingSafeEqual;
  if (typeof timingSafeEqual === "function") {
    try {
      return timingSafeEqual.call(crypto.subtle, left, right);
    } catch {
      /* Lengths are already fixed by SHA-256. A runtime that rejects the
         BufferSource still compares the same 32 bytes below. */
    }
  }
  let diff = 0;
  for (let i = 0; i < left.length; i++) diff |= left[i] ^ right[i];
  return diff === 0;
}

export function corsHeaders(request) {
  const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
  const headers = {
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "content-type, x-agentscout-app",
    "access-control-max-age": "86400",
    vary: "Origin",
  };
  if (origin) headers["access-control-allow-origin"] = origin;
  return headers;
}

function clientIp(request) {
  return (request.headers.get("cf-connecting-ip") || "").trim();
}

// Hide TURNSTILE_ENABLED from the inner handler only on the POSTs protect()
// already siteverified. The token is single-use; a second check on /submit or
// /generate rejects a real visitor. Every other path sees the real flag.
export function maskTurnstileEnv(request, env) {
  let path = "";
  try { path = normalizePath(new URL(request.url).pathname); } catch { return env; }
  if (!request || request.method !== "POST" || !TURNSTILE_PATHS.has(path)) return env;
  return new Proxy(env, { get: (target, key) => (key === "TURNSTILE_ENABLED" ? "false" : target[key]) });
}

function withSecurity(headers) {
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) headers.set(key, value);
  return headers;
}

function json(request, body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: withSecurity(new Headers({
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...corsHeaders(request),
    })),
  });
}

function seal(response) {
  const headers = withSecurity(new Headers(response.headers));
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

function reviewPost(pathname, method) {
  if (method !== "POST") return false;
  const path = normalizePath(pathname);
  return path === "/review" || path === "/reviews";
}

function trackedPost(pathname, method) {
  if (method !== "POST") return false;
  const path = normalizePath(pathname);
  return path === "/track" || path === "/share";
}

async function limitedBody(request, max) {
  const declared = Number(request.headers.get("content-length"));
  if (Number.isFinite(declared) && declared > max) return { error: "too_large" };
  if (!request.body) return { request };
  const reader = request.body.getReader();
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
  const headers = new Headers(request.headers);
  headers.delete("content-length");
  return { request: new Request(request, { body: buf, headers }) };
}

async function readinessQuota(request, env) {
  const limiter = env && env.IMAGE_READ;
  if (!limiter || typeof limiter.limit !== "function") return null;
  const ip = clientIp(request);
  if (!ip) return null;
  let result;
  try {
    result = await limiter.limit({ key: ip });
  } catch {
    return json(request, { error: "Rate limiting is not configured." }, 503);
  }
  if (!result || result.success !== true) return json(request, { error: "Too many requests. Try again in a minute." }, 429);
  return null;
}

function isRead(method) {
  return method === "GET" || method === "HEAD";
}

async function consume(limiter, ip) {
  if (!limiter || typeof limiter.limit !== "function") return "unconfigured";
  let result;
  try {
    result = await limiter.limit({ key: ip });
  } catch {
    return "unconfigured";
  }
  if (!result || result.success !== true) return "limited";
  return "ok";
}

async function rejectStatsKey(request, env) {
  if (!statsKeyPath(new URL(request.url).pathname)) return null;
  const provided = request.headers.get("X-Stats-Key");
  const expected = env && env.STATS_KEY;
  if (!(await safeEq(provided, expected))) return json(request, { error: "Forbidden." }, 403);
  return null;
}

async function turnstileToken(request) {
  const length = Number(request.headers.get("content-length") || "0");
  if (Number.isFinite(length) && length > MAX_TURNSTILE_BODY) return "";
  let text = "";
  try {
    text = await request.clone().text();
  } catch {
    return "";
  }
  if (text.length > MAX_TURNSTILE_BODY) return "";
  try {
    const data = JSON.parse(text);
    const token = data && typeof data === "object" ? data.turnstileToken : "";
    return typeof token === "string" ? token : "";
  } catch {
    return "";
  }
}

async function rejectTurnstile(request, env) {
  if (!turnstileEnabled(env)) return null;
  const url = new URL(request.url);
  if (request.method !== "POST" || !TURNSTILE_PATHS.has(normalizePath(url.pathname))) return null;
  const secret = env && env.TURNSTILE_SECRET;
  const token = await turnstileToken(request);
  const ip = clientIp(request);
  if (typeof secret !== "string" || !secret || !token || token.length > MAX_TURNSTILE_TOKEN || !ip) {
    return json(request, { error: "Bot check failed." }, 403);
  }
  let data = null;
  try {
    const response = await fetch(SITEVERIFY_URL, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        secret,
        response: token,
        remoteip: ip,
      }),
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return json(request, { error: "Bot check failed." }, 403);
    data = await response.json();
  } catch {
    return json(request, { error: "Bot check failed." }, 403);
  }
  return turnstileRejection(request, data, expectedTurnstileAction(url.pathname));
}

// /submit tokens are minted with action "submit". Other actions, and tokens
// minted by the review or generate widgets on this same sitekey, are rejected.
// /generate still accepts any successful token for this hostname.
export function expectedTurnstileAction(pathname) {
  return normalizePath(pathname) === "/submit" ? SUBMIT_ACTION : "";
}

export function turnstileRejection(request, data, expectedAction) {
  const host = String((data && data.hostname) || "").toLowerCase();
  const actionOk = !expectedAction || (data && data.action === expectedAction);
  if (data && data.success === true && ALLOWED_HOSTS.has(host) && actionOk) return null;
  if (data && data.success === true && ALLOWED_HOSTS.has(host) && !actionOk) {
    return json(request, { error: TURNSTILE_STALE_PAGE }, 403);
  }
  const codes = data && Array.isArray(data["error-codes"]) ? data["error-codes"] : [];
  const retry = !!(data && data.success !== true && codes.some((code) =>
    code === "timeout-or-duplicate" || code === "invalid-input-response"));
  return json(request, { error: retry ? TURNSTILE_RETRY_ERROR : "Bot check failed." }, 403);
}

async function rejectReadiness(request) {
  const url = new URL(request.url);
  if (normalizePath(url.pathname) !== "/readiness" || !url.searchParams.has("url")) return null;
  const rawUrl = url.searchParams.get("url") || "";
  if (rawUrl.length > MAX_READY_URL) return json(request, { error: "That address is not a valid URL." }, 400);
  const shape = validateUrlShape(rawUrl);
  if (shape.error) return json(request, { error: shape.error }, 400);
  const host = shape.url.hostname.replace(/^\[|\]$/g, "");
  try {
    const dns = await resolveAndCheck(host);
    if (dns.error) return json(request, { error: dns.error }, 400);
  } catch {
    return json(request, { error: "Could not look up that host." }, 400);
  }
  return null;
}

async function limitByIp(request, env) {
  const ip = clientIp(request);
  if (!ip) return json(request, { error: "Client address is unavailable." }, 403);
  const limiter = isRead(request.method) ? env && env.IMAGE_READ : env && env.IMAGE_WRITE;
  const outcome = await consume(limiter, ip);
  if (outcome === "unconfigured") return json(request, { error: "Rate limiting is not configured." }, 503);
  if (outcome === "limited") return json(request, { error: "Too many requests. Try again in a minute." }, 429);
  return null;
}

export async function gate(request, env) {
  const url = new URL(request.url);
  if (!requestGuarded(url.pathname, request.method)) return null;
  if (request.method === "OPTIONS") {
    const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
    if (!origin) return new Response(null, { status: 403, headers: withSecurity(new Headers({ vary: "Origin" })) });
    return new Response(null, { status: 204, headers: withSecurity(new Headers(corsHeaders(request))) });
  }
  const limited = await limitByIp(request, env);
  if (limited) return limited;
  if (request.method === "POST" && !postAllowed(request)) {
    return json(request, { error: "Submissions can only be sent from agentscouthq.com." }, 403);
  }
  return null;
}

export function applyCors(request, response) {
  const headers = new Headers(response.headers);
  headers.delete("access-control-allow-origin");
  const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
  if (origin) headers.set("access-control-allow-origin", origin);
  const vary = headers.get("vary");
  if (!vary) headers.set("vary", "Origin");
  else if (!vary.split(",").some((part) => part.trim().toLowerCase() === "origin")) headers.set("vary", vary + ", Origin");
  headers.set("access-control-allow-methods", "GET, POST, OPTIONS");
  headers.set("access-control-allow-headers", "content-type, x-agentscout-app");
  headers.set("access-control-max-age", "86400");
  withSecurity(headers);
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

function adminCors(request, response) {
  const headers = withSecurity(new Headers(response.headers));
  headers.delete("access-control-allow-origin");
  const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
  if (origin) headers.set("access-control-allow-origin", origin);
  const vary = headers.get("vary");
  if (!vary) headers.set("vary", "Origin");
  else if (!vary.split(",").some((part) => part.trim().toLowerCase() === "origin")) headers.set("vary", vary + ", Origin");
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

const READINESS_UA = "AgentScoutReadinessChecker/";
let fetchDelegate = null;

function requestUrl(input) {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  if (input && typeof input.url === "string") return input.url;
  return "";
}

function headerValue(init, name) {
  const headers = init && init.headers;
  if (!headers) return "";
  if (typeof headers.get === "function") return headers.get(name) || "";
  const target = name.toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === target) return String(headers[key] || "");
  }
  return "";
}

// DNS lookup and the following fetch are still two steps. The runtime resolves
// the name again. Connecting to the looked-up address would skip the certificate
// check for the hostname, so this does not pin the address. A change between
// the lookup and the fetch is still possible.
export async function guardedPublicFetch(original, input, init) {
  if (!headerValue(init, "user-agent").startsWith(READINESS_UA)) return original(input, init);
  const shape = validateUrlShape(requestUrl(input));
  if (shape.error) throw new Error("blocked public fetch");
  const dns = await resolveAndCheck(shape.url.hostname, original);
  if (dns.error) throw new Error("blocked public fetch");
  return original(input, init);
}

function installFetchGuard() {
  const current = globalThis.fetch;
  if (current && current.__agentscoutPublicFetch) return;
  fetchDelegate = current.bind(globalThis);
  const guarded = (input, init) => guardedPublicFetch(fetchDelegate, input, init);
  guarded.__agentscoutPublicFetch = true;
  globalThis.fetch = guarded;
}

function failClosedLimit(binding) {
  if (!binding || typeof binding.limit !== "function") return binding;
  return {
    async limit(arg) {
      try {
        const result = await binding.limit(arg);
        return result && result.success === true ? { success: true } : { success: false };
      } catch {
        return { success: false };
      }
    },
  };
}

function failClosedReady(namespace) {
  if (!namespace || typeof namespace.get !== "function") return namespace;
  return {
    idFromName(name) {
      return namespace.idFromName(name);
    },
    get(id) {
      const stub = namespace.get(id);
      return {
        async fetch(...args) {
          try {
            const response = await stub.fetch(...args);
            const data = await response.json();
            const body = data && data.ok === true ? data : { ok: false, retry: data && data.retry };
            return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
          } catch {
            return new Response(JSON.stringify({ ok: false, retry: 60 }), { status: 200, headers: { "content-type": "application/json" } });
          }
        },
      };
    },
  };
}

export function hardenLimiters(env) {
  if (!env || typeof env !== "object") return env;
  return new Proxy(env, {
    get(target, key) {
      if (key === "REVIEW_RL" || key === "TRACK_RL" || key === "READY_RL") return failClosedLimit(target[key]);
      if (key === "READY_LIMIT") return failClosedReady(target[key]);
      return target[key];
    },
  });
}

export function protect(worker) {
  if (!worker || typeof worker.fetch !== "function") {
    throw new TypeError("protect() expects the existing worker export");
  }
  const inner = worker.fetch.bind(worker);
  return {
    async fetch(request, env, ctx) {
      try {
      const path = normalizePath(new URL(request.url).pathname);
      if (path === EXPORT_PATH && !exportEnabled(env)) {
        return new Response(JSON.stringify({ error: "Not found." }), {
          status: 404,
          headers: withSecurity(new Headers({
            "content-type": "application/json; charset=utf-8",
            "cache-control": "private, no-store",
          })),
        });
      }
      // Count a guess against IMAGE_READ/IMAGE_WRITE before comparing X-Stats-Key.
      // Guarded stats paths (/reviews/pending, /reviews/admin, /reviews/export) are
      // counted again by gate(). A person checking pending reviews stays under 120/min.
      if (statsKeyPath(path) && request.method !== "OPTIONS") {
        const limited = await limitByIp(request, env);
        if (limited) return limited;
      }
      const statsBlocked = await rejectStatsKey(request, env);
      if (statsBlocked) return statsBlocked;
      const blocked = await gate(request, env);
      if (blocked) return blocked;
      if (normalizePath(new URL(request.url).pathname) === EXPORT_PATH) return handleReviewsExport(request, env);
      const turnstileBlocked = await rejectTurnstile(request, env);
      if (turnstileBlocked) return turnstileBlocked;
      let next = request;
      const pathNow = normalizePath(new URL(request.url).pathname);
      if (reviewPost(pathNow, request.method) || trackedPost(pathNow, request.method)) {
        const capped = await limitedBody(request, reviewPost(pathNow, request.method) ? MAX_REVIEW_BODY : MAX_TRACK_BODY);
        if (capped.error) return json(request, { error: "Payload too large." }, capped.error === "too_large" ? 413 : 400);
        next = capped.request;
      }
      if ((request.method === "GET" || request.method === "HEAD") && pathNow === "/readiness") {
        const quota = await readinessQuota(request, env);
        if (quota) return quota;
      }
      const readinessBlocked = await rejectReadiness(next);
      if (readinessBlocked) return readinessBlocked;
      installFetchGuard();
      let response;
      try {
        response = await inner(next, hardenLimiters(maskTurnstileEnv(next, env)), ctx);
      } catch {
        console.error(JSON.stringify({ message: "image request failed", path: pathNow, status: 500 }));
        return json(next, { error: "The request failed." }, 500);
      }
      if (statsKeyPath(pathNow) && !requestGuarded(pathNow, request.method)) return adminCors(next, response);
      if (!requestGuarded(pathNow, request.method)) return seal(response);
      return applyCors(next, response);
      } catch {
        console.error(JSON.stringify({ message: "image request failed", status: 500 }));
        return new Response(JSON.stringify({ error: "The request failed." }), {
          status: 500,
          headers: withSecurity(new Headers({
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
          })),
        });
      }
    },
  };
}
