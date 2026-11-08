import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createBackupDO, parseBackupRequest, readBackupPage, readConsistentSnapshot, snapshotEnabled } from "./reviews-backup.js";

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

function storageOf(tables, options = {}) {
  const calls = [];
  return {
    calls,
    sql: {
      exec(query) {
        calls.push(query);
        if (options.throwOn) throw new Error("leak synthetic-body-token");
        const rows = tables[query] || [];
        const cursor = { toArray() { return rows; } };
        if (options.rowsWritten !== "omit") cursor.rowsWritten = options.rowsWritten ?? 0;
        return cursor;
      },
    },
    transactionSync(fn) {
      calls.push("transactionSync");
      return fn();
    },
  };
}

test("the snapshot reads both tables in one synchronous transaction and drops extra columns", () => {
  const ratingsSql = "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid";
  const reviewsSql = "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id";
  const storage = storageOf({
    [ratingsSql]: [{ tool: "cursor", vid: "aa", iph: "bb", stars: 5, ts: 1, secret: "nope" }],
    [reviewsSql]: [{ id: "r1", tool: "cursor", vid: "aa", iph: "bb", stars: 5, name: "A", body: "synthetic-body-token", status: "pending", ts: 1 }],
  });
  const snap = readConsistentSnapshot(storage);
  assert.equal(snap.rows_written, 0);
  assert.equal(snap.ratings[0].secret, undefined);
  assert.equal(storage.calls[0], "transactionSync");
  assert.equal(storage.calls.includes(ratingsSql), true);
  assert.equal(storage.calls.includes(reviewsSql), true);
  assert.equal(storage.calls.some((query) => String(query).includes("limits")), false);
});

test("snapshot stays disabled and a storage error does not echo row text", () => {
  class Base { constructor() { this.sql = {}; this.env = {}; this.ctx = { storage: { transactionSync() { throw new Error("no"); } } }; } }
  const ReviewsDO = createBackupDO(Base);
  assert.throws(() => new ReviewsDO().snapshotRatingsReviews(), (error) => error.code === "snapshot_disabled");
  const enabled = new ReviewsDO();
  enabled.env = { REVIEWS_SNAPSHOT: "true" };
  assert.throws(() => enabled.snapshotRatingsReviews(), (error) => error.code === "snapshot_unavailable");
  const leaking = storageOf({}, { throwOn: true });
  assert.throws(() => readConsistentSnapshot(leaking), (error) => error.code === "snapshot_failed" && !error.message.includes("synthetic-body-token"));
  const wrote = storageOf({
    "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid": [],
    "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id": [],
  }, { rowsWritten: 1 });
  assert.throws(() => readConsistentSnapshot(wrote), (error) => error.code === "rows_written");
  const missingCount = storageOf({
    "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid": [],
    "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id": [],
  }, { rowsWritten: "omit" });
  assert.throws(() => readConsistentSnapshot(missingCount), (error) => error.code === "rows_written");
  const malformed = storageOf({
    "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid": [{ tool: "cursor" }],
    "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id": [],
  });
  assert.throws(() => readConsistentSnapshot(malformed), (error) => error.code === "bad_row");
  const tooMany = Array.from({ length: 10001 }, (_, index) => ({ tool: "t", vid: String(index), iph: "i", stars: 1, ts: 1 }));
  const overCap = storageOf({
    "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid": tooMany,
    "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id": [],
  });
  assert.throws(() => readConsistentSnapshot(overCap), (error) => error.code === "records_cap");
  const heavy = Array.from({ length: 4200 }, (_, index) => ({
    id: String(index), tool: "t", vid: "v", iph: "i", stars: 1, name: "n", body: "x".repeat(8000), status: "pending", ts: 1,
  }));
  const overSize = storageOf({
    "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid": [],
    "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id": heavy,
  });
  assert.throws(() => readConsistentSnapshot(overSize), (error) => error.code === "size_cap" && !String(error.message).includes("xxxx"));
  assert.equal(snapshotEnabled(undefined), false);
  assert.equal(snapshotEnabled({ REVIEWS_SNAPSHOT: "TRUE" }), false);
  assert.equal(snapshotEnabled({ REVIEWS_SNAPSHOT: "true" }), true);
  const asyncTxn = storageOf({}, {});
  asyncTxn.transactionSync = () => Promise.resolve({ ratings: [], reviews: [] });
  assert.throws(() => readConsistentSnapshot(asyncTxn), (error) => error.code === "snapshot_unavailable");
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