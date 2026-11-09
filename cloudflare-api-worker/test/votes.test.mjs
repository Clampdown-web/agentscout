import test from "node:test";
import assert from "node:assert/strict";
import worker, { allowOrigin, parseSlugs, normalizeStored, castInDoc, countsFor, isoWeek } from "../src/worker.js";

test("cors allowlist is the site and www only", () => {
  assert.equal(allowOrigin("https://agentscouthq.com"), "https://agentscouthq.com");
  assert.equal(allowOrigin("https://www.agentscouthq.com"), "https://www.agentscouthq.com");
  assert.equal(allowOrigin("https://evil.example"), "");
  assert.equal(allowOrigin("https://agentscouthq.com.evil"), "");
  assert.equal(allowOrigin(""), "");
});

test("iso week key matches the Pacific date's ISO week", () => {
  assert.equal(isoWeek("2026-10-30"), "2026-w44");
  assert.equal(isoWeek("2026-10-26"), "2026-w44");
  assert.equal(isoWeek("2026-11-02"), "2026-w45");
});

test("slug list is unique and capped at 400", () => {
  const raw = Array.from({ length: 450 }, (_, i) => `tool-${i}`).join(",");
  const slugs = parseSlugs(raw + ",tool-1,not a slug");
  assert.equal(slugs.length, 400);
  assert.equal(slugs[0], "tool-0");
  assert.equal(slugs.includes("not"), false);
});

test("week document is one map, and today resets when the day changes", () => {
  const stored = normalizeStored({ day: "2026-10-30", week: { sickle: 3 }, today: { sickle: 1 } }, "2026-10-30");
  assert.equal(stored.week.sickle, 3);
  assert.equal(stored.today.sickle, 1);
  const nextDay = normalizeStored({ day: "2026-10-30", week: { sickle: 3 }, today: { sickle: 1 } }, "2026-10-31");
  assert.equal(nextDay.day, "");
  assert.equal(nextDay.week.sickle, 3);
  assert.deepEqual(nextDay.today, {});
  const voted = castInDoc(nextDay, "sickle", "2026-10-31");
  assert.equal(voted.week.sickle, 4);
  assert.equal(voted.today.sickle, 1);
  assert.equal(voted.day, "2026-10-31");
  const again = castInDoc(voted, "other-tool", "2026-10-31");
  assert.equal(again.week.sickle, 4);
  assert.equal(again.week["other-tool"], 1);
  assert.equal(again.today.sickle, 1);
});

test("public counts omit the visitor flag", () => {
  const doc = castInDoc(normalizeStored(null, "2026-10-30"), "sickle", "2026-10-30");
  const counts = countsFor(doc, ["sickle", "missing"], "2026-10-30");
  assert.deepEqual(counts.tools.sickle, { votes: 1, today: 1 });
  assert.equal("yours" in counts.tools.sickle, false);
  assert.equal(counts.tools.missing.votes, 0);
  assert.equal(counts.today_total, 1);
});

function memoryKv() {
  const store = new Map();
  return {
    async get(key, type) {
      if (!store.has(key)) return null;
      const value = store.get(key);
      return type === "json" ? JSON.parse(value) : value;
    },
    async put(key, value) { store.set(key, String(value)); },
    get size() { return store.size; },
  };
}

function voteRequest(extra = {}) {
  const headers = { "content-type": "application/json", "cf-connecting-ip": "203.0.113.8" };
  for (const [key, value] of Object.entries(extra)) headers[key] = value;
  return new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers,
    body: JSON.stringify({ slug: "sickle" }),
  });
}

test("an allowed origin can vote", async () => {
  const kv = memoryKv();
  const res = await worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: kv });
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.ok, true);
  assert.equal(body.slug, "sickle");
  assert.equal(body.votes, 1);
  assert.equal(body.already, false);
  const again = await worker.fetch(voteRequest({ origin: "https://www.agentscouthq.com" }), { VOTES: kv });
  const second = await again.json();
  assert.equal(again.status, 200);
  assert.equal(second.already, true);
  assert.equal(second.votes, 1);
});

test("a missing origin gets a 403", async () => {
  const kv = memoryKv();
  const res = await worker.fetch(voteRequest(), { VOTES: kv });
  assert.equal(res.status, 403);
  assert.equal(kv.size, 0);
});

test("a forwarded address is not a voter and a missing salt fails closed", async () => {
  const kv = memoryKv();
  const forwarded = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { "content-type": "application/json", origin: "https://agentscouthq.com", "x-forwarded-for": "198.51.100.9" },
    body: JSON.stringify({ slug: "sickle" }),
  }), { VOTES: kv });
  assert.equal(forwarded.status, 403);
  assert.equal(kv.size, 0);
  const blind = {
    async get() { return null; },
    async put(key) { kv.put(key, "written"); },
  };
  const res = await worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: blind });
  assert.equal(res.status, 503);
  assert.equal((await res.json()).error, "Vote storage is not ready.");
});

test("overlapping votes for one visitor increment the tally once", async () => {
  const kv = memoryKv();
  const [first, second] = await Promise.all([
    worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: kv }),
    worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: kv }),
  ]);
  const bodies = [await first.json(), await second.json()];
  assert.equal(first.status, 200);
  assert.equal(second.status, 200);
  assert.equal(bodies.filter((body) => body.already).length, 1);
  assert.equal(bodies.filter((body) => body.votes === 1).length, 2);
});

test("a second seen-key write that conflicts does not increment again", async () => {
  let seenPuts = 0;
  const store = new Map();
  const kv = {
    async get(key, type) {
      if (!store.has(key)) return null;
      const value = store.get(key);
      return type === "json" ? JSON.parse(value) : value;
    },
    async put(key, value) {
      if (String(key).startsWith("seen:")) {
        seenPuts += 1;
        if (seenPuts > 1) throw new Error("KV PUT failed: 429 Too Many Requests");
      }
      store.set(key, String(value));
    },
  };
  const [first, second] = await Promise.all([
    worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: kv }),
    worker.fetch(voteRequest({ origin: "https://agentscouthq.com" }), { VOTES: kv }),
  ]);
  const bodies = [await first.json(), await second.json()];
  assert.equal(bodies.filter((body) => body.ok && !body.already).length, 1);
  assert.equal(Math.max(...bodies.map((body) => body.votes)), 1);
});

test("evil.com gets a 403", async () => {
  const kv = memoryKv();
  const res = await worker.fetch(voteRequest({ origin: "https://evil.com" }), { VOTES: kv });
  assert.equal(res.status, 403);
  const body = await res.json();
  assert.equal(body.error, "Votes can only be cast from agentscouthq.com.");
  assert.equal(kv.size, 0);
});

function assertVoteCors(res, origin) {
  assert.equal(res.headers.get("access-control-allow-methods"), "GET, POST, OPTIONS");
  assert.equal(res.headers.get("access-control-allow-headers"), "content-type");
  assert.equal(res.headers.get("vary"), "Origin");
  if (origin) assert.equal(res.headers.get("access-control-allow-origin"), origin);
  else assert.equal(res.headers.get("access-control-allow-origin"), null);
  assert.equal(res.headers.get("access-control-allow-credentials"), null);
}

test("public vote routes keep status, JSON shape, and CORS", async () => {
  const kv = memoryKv();
  const origin = "https://agentscouthq.com";
  const ip = "203.0.113.60";
  const preflight = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "OPTIONS",
    headers: { origin, "access-control-request-headers": "content-type" },
  }), { VOTES: kv });
  assert.equal(preflight.status, 204);
  assert.equal(await preflight.text(), "");
  assertVoteCors(preflight, origin);
  assert.equal(preflight.headers.get("access-control-max-age"), "86400");

  const foreign = await worker.fetch(new Request("https://votes.agentscouthq.com/votes", {
    method: "OPTIONS",
    headers: { origin: "https://evil.example" },
  }), { VOTES: kv });
  assert.equal(foreign.status, 204);
  assertVoteCors(foreign, "");

  const counts = await worker.fetch(new Request("https://votes.agentscouthq.com/votes?slugs=sickle,cursor", {
    headers: { origin, "cf-connecting-ip": ip },
  }), { VOTES: kv });
  assert.equal(counts.status, 200);
  assert.equal(counts.headers.get("content-type"), "application/json; charset=utf-8");
  assert.equal(counts.headers.get("cache-control"), "public, max-age=60");
  assertVoteCors(counts, origin);
  const listed = await counts.json();
  assert.equal(listed.ok, true);
  assert.equal(listed.week, isoWeek(listed.day));
  assert.deepEqual(listed.tools.sickle, { votes: 0, today: 0 });
  assert.deepEqual(listed.tools.cursor, { votes: 0, today: 0 });
  assert.equal(listed.today_total, 0);
  assert.equal(listed.yours, undefined);
  assert.equal(listed.storage, undefined);

  const slashed = await worker.fetch(new Request("https://votes.agentscouthq.com/votes/?slugs=sickle", {
    headers: { origin: "https://www.agentscouthq.com" },
  }), { VOTES: kv });
  assert.equal(slashed.status, 200);
  assert.equal((await slashed.json()).tools.sickle.votes, 0);
  assertVoteCors(slashed, "https://www.agentscouthq.com");

  const bare = await worker.fetch(new Request("https://votes.agentscouthq.com/votes?slugs=sickle"), { VOTES: kv });
  assert.equal(bare.status, 200);
  assertVoteCors(bare, "");

  const unconfigured = await worker.fetch(new Request("https://votes.agentscouthq.com/votes?slugs=sickle", {
    headers: { origin },
  }), {});
  assert.equal(unconfigured.status, 200);
  assert.equal(unconfigured.headers.get("cache-control"), "no-store");
  const empty = await unconfigured.json();
  assert.equal(empty.ok, true);
  assert.equal(empty.storage, "unconfigured");
  assert.deepEqual(empty.tools.sickle, { votes: 0, today: 0 });

  const cast = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": ip },
    body: JSON.stringify({ slug: "sickle" }),
  }), { VOTES: kv });
  assert.equal(cast.status, 200);
  assert.equal(cast.headers.get("content-type"), "application/json; charset=utf-8");
  assert.equal(cast.headers.get("cache-control"), "no-store");
  assertVoteCors(cast, origin);
  const voted = await cast.json();
  assert.equal(voted.ok, true);
  assert.equal(voted.slug, "sickle");
  assert.equal(voted.votes, 1);
  assert.equal(voted.today, 1);
  assert.equal(voted.already, false);
  assert.equal(voted.yours, true);
  assert.equal(typeof voted.week, "string");

  const badSlug = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": "203.0.113.61" },
    body: JSON.stringify({ slug: "Not A Slug" }),
  }), { VOTES: kv });
  assert.equal(badSlug.status, 400);
  assert.deepEqual(await badSlug.json(), { error: "Unknown tool." });
  assertVoteCors(badSlug, origin);

  const missing = await worker.fetch(new Request("https://votes.agentscouthq.com/nope", {
    headers: { origin },
  }), { VOTES: kv });
  assert.equal(missing.status, 404);
  assert.deepEqual(await missing.json(), { error: "Not found", endpoints: ["/roast", "/vote", "/votes"] });
  assertVoteCors(missing, origin);

  const wrongVote = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    headers: { origin },
  }), { VOTES: kv });
  assert.equal(wrongVote.status, 404);
  const wrongCounts = await worker.fetch(new Request("https://votes.agentscouthq.com/votes", {
    method: "POST",
    headers: { origin, "content-type": "application/json" },
    body: "{}",
  }), { VOTES: kv });
  assert.equal(wrongCounts.status, 404);
  assert.equal(cast.headers.get("x-content-type-options"), "nosniff");
  assert.equal(cast.headers.get("x-frame-options"), "DENY");
  assert.equal(cast.headers.get("referrer-policy"), "strict-origin-when-cross-origin");
});

test("vote and count inputs over the limit are rejected without a stack", async () => {
  const kv = memoryKv();
  const origin = "https://agentscouthq.com";
  const huge = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": "203.0.113.80" },
    body: JSON.stringify({ slug: "sickle", pad: "x".repeat(20_000) }),
  }), { VOTES: kv });
  assert.equal(huge.status, 413);
  const hugeBody = await huge.json();
  assert.deepEqual(hugeBody, { error: "Payload too large." });
  assert.equal(JSON.stringify(hugeBody).includes("pad"), false);

  const slugs = "a".repeat(40_001);
  const many = await worker.fetch(new Request("https://votes.agentscouthq.com/votes?slugs=" + slugs, {
    headers: { origin },
  }), { VOTES: kv });
  assert.equal(many.status, 400);
  assert.deepEqual(await many.json(), { error: "Too many tools." });

  const broken = {
    async get() { throw new Error("postgres://user:secret-token@internal/db"); },
    async put() { throw new Error("postgres://user:secret-token@internal/db"); },
  };
  const leaked = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": "203.0.113.81" },
    body: JSON.stringify({ slug: "sickle" }),
  }), { VOTES: broken });
  assert.equal(leaked.status, 500);
  const text = await leaked.text();
  assert.equal(text.includes("secret-token"), false);
  assert.equal(text.includes("postgres"), false);
  assert.equal(text.includes("Error"), false);
  assert.deepEqual(JSON.parse(text), { error: "The check failed. Try again in a minute." });

  const fresh = memoryKv();
  const longIp = await worker.fetch(new Request("https://votes.agentscouthq.com/vote", {
    method: "POST",
    headers: { origin, "content-type": "application/json", "cf-connecting-ip": "x".repeat(200) },
    body: JSON.stringify({ slug: "sickle" }),
  }), { VOTES: fresh });
  assert.equal(longIp.status, 403);
  assert.equal(fresh.size, 0);
});
