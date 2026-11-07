import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createBackupDO, parseBackupRequest, readBackupPage } from "./reviews-backup.js";

function sqlOf(rows) {
  const calls = [];
  return {
    calls,
    exec(query, ...args) {
      calls.push({ query, args });
      return { toArray() { return rows; } };
    },
  };
}

test("backup queries are fixed per table and drop unexpected columns", () => {
  const parsed = parseBackupRequest(new URL("https://api.agentscouthq.com/reviews/export?table=ratings&limit=2"));
  assert.equal(parsed.error, undefined);
  const page = readBackupPage(sqlOf([{ tool: "cursor", vid: "ab", iph: "hash", stars: 5, ts: 1, secret: "nope" }]), parsed);
  assert.equal(page.rows[0].secret, undefined);
  assert.deepEqual(page.rows, [{ tool: "cursor", vid: "ab", iph: "hash", stars: 5, ts: 1 }]);
  assert.equal(page.next, null);
  const bad = parseBackupRequest(new URL("https://api.agentscouthq.com/reviews/export?table=ratings%3Bdrop&limit=1000"));
  assert.equal(bad.error, "Unknown table.");
  const huge = parseBackupRequest(new URL("https://api.agentscouthq.com/reviews/export?table=limits&limit=101"));
  assert.equal(huge.error, "Bad limit.");
  const injected = parseBackupRequest(new URL("https://api.agentscouthq.com/reviews/export?table=reviews&cursor=not-json"));
  assert.equal(injected.error, "Bad cursor.");
});

test("a full page returns a cursor the next call accepts", () => {
  const first = readBackupPage(sqlOf([
    { id: "a", tool: "cursor", vid: "ab", iph: "h", stars: 4, name: "", body: "hello", status: "pending", ts: 1 },
  ]), { table: "reviews", limit: 1, cursor: { id: "" } });
  assert.ok(first.next);
  const again = parseBackupRequest(new URL("https://api.agentscouthq.com/reviews/export?table=reviews&cursor=" + first.next));
  assert.equal(again.error, undefined);
  assert.equal(again.cursor.id, "a");
  const store = sqlOf([]);
  readBackupPage(store, again);
  assert.match(store.calls[0].query, /^SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews WHERE id > \?/);
  assert.deepEqual(store.calls[0].args, ["a", 100]);
});

test("the subclass reads through the base sql handle and rejects a bad spec", async () => {
  const store = sqlOf([{ k: "mn:abc:2026-11-07T18:43", n: 1, exp: 5, token: "nope" }]);
  class Base {
    constructor() { this.sql = store; }
  }
  const ReviewsDO = createBackupDO(Base);
  const page = await new ReviewsDO().backupPage({ table: "limits", limit: 10, cursor: { k: "" } });
  assert.equal(page.rows[0].token, undefined);
  assert.equal(page.rows[0].k, "mn:abc:2026-11-07T18:43");
  await assert.rejects(() => new ReviewsDO().backupPage({ table: "sqlite_master", limit: 10, cursor: {} }));
});

test("the recovery plan does not embed a secret value", () => {
  const text = readFileSync(new URL("../docs/recovery-plan.md", import.meta.url), "utf8");
  assert.equal(/BEGIN [A-Z ]*PRIVATE KEY/.test(text), false);
  assert.equal(text.includes("sk_live"), false);
  assert.equal(text.includes("TURNSTILE_SECRET="), false);
  assert.equal(text.includes("STATS_KEY="), false);
  assert.match(text, /1c6368ca-f9d5-403e-92c2-7954641c2153/);
  assert.match(text, /agentscout-x-media/);
  assert.match(text, /b470d63a005a4d548e00f488e1a888e3/);
  assert.match(text, /Worker error alerts are not enabled/);
  assert.match(text, /value was not read/);
});