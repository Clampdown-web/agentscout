/**
 * Drop-in guard for the agentscout-image worker (api.agentscouthq.com).
 * The worker source is not in this repo. Wrap its export with protect().
 *
 * Guards /submit, /review, and /reviews (the review form posts to /review).
 * Other routes (/generate, /track, /readiness, /geo, /share, /stats) are unchanged.
 *
 * Bindings (Workers Rate Limiting, per CF-Connecting-IP):
 *   IMAGE_WRITE  10 requests / 60s   POST and other non-read methods
 *   IMAGE_READ  120 requests / 60s   GET and HEAD
 * A missing binding fails closed with 503. There is no User-Agent bypass.
 */
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

export function guardedKind(pathname) {
  const path = String(pathname || "/").replace(/\/+$/, "") || "/";
  if (path === "/submit") return "submit";
  if (path === "/review" || path === "/reviews" || path.startsWith("/reviews/")) return "reviews";
  return "";
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
  return request.headers.get("cf-connecting-ip")
    || (request.headers.get("x-forwarded-for") || "").split(",")[0].trim()
    || "0.0.0.0";
}

function json(request, body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...corsHeaders(request),
    },
  });
}

function isRead(method) {
  return method === "GET" || method === "HEAD";
}

async function consume(limiter, ip) {
  if (!limiter || typeof limiter.limit !== "function") return "unconfigured";
  const result = await limiter.limit({ key: ip });
  return result && result.success === false ? "limited" : "ok";
}

export async function gate(request, env) {
  if (!guardedKind(new URL(request.url).pathname)) return null;
  if (request.method === "OPTIONS") {
    const origin = allowOrigin(request.headers.get("Origin") || request.headers.get("origin") || "");
    if (!origin) return new Response(null, { status: 403, headers: { vary: "Origin" } });
    return new Response(null, { status: 204, headers: corsHeaders(request) });
  }
  const limiter = isRead(request.method) ? env && env.IMAGE_READ : env && env.IMAGE_WRITE;
  const outcome = await consume(limiter, clientIp(request));
  if (outcome === "unconfigured") return json(request, { error: "Rate limiting is not configured." }, 503);
  if (outcome === "limited") return json(request, { error: "Too many requests. Try again in a minute." }, 429);
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
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export function protect(worker) {
  if (!worker || typeof worker.fetch !== "function") {
    throw new TypeError("protect() expects the existing worker export");
  }
  const inner = worker.fetch.bind(worker);
  return {
    async fetch(request, env, ctx) {
      const blocked = await gate(request, env);
      if (blocked) return blocked;
      const response = await inner(request, env, ctx);
      if (!guardedKind(new URL(request.url).pathname)) return response;
      return applyCors(request, response);
    },
  };
}
