import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { randomBytes } from "node:crypto";
import { planProviderReads, sendProvider } from "./allowlist.mjs";
import { capture, retentionDue } from "./capture.mjs";
import { reopenCounts, restoreBytes } from "./restore.mjs";

const EMAIL = "maker@example.test";
const BODY = "synthetic review body";

function fixture(extra = {}) {
  return {
    roundTrips: 1,
    responses: [
      {
        id: "ratings",
        rows_written: 0,
        rows: [
          { tool: "cursor", vid: "ab", iph: "cd", stars: 5, ts: 1 },
          { tool: "koog", vid: "ef", iph: "11", stars: 4, ts: 2 },
        ],
      },
      {
        id: "reviews",
        rows_written: 0,
        rows: [
          { id: "a1", tool: "cursor", vid: "ab", iph: "cd", stars: 5, name: "Ada", body: BODY, status: "pending", ts: 1 },
          { id: "b2", tool: "koog", vid: "ef", iph: "11", stars: 2, name: "Bea", body: "no", status: "rejected", ts: 2 },
        ],
      },
    ],
    submissions: [
      {
        key: "sub:one",
        expiration: 2_000_000_000,
        value: {
          ts: "1", type: "new", tool: "cursor", name: "Ada", website: "https://example.test",
          github: "", category: "coding", pricing: "free", desc: "synthetic", email: EMAIL,
          x: "", found: "readme", found_other: "", found_flag: "",
        },
      },
      {
        key: "sub:old",
        expiration: 10,
        value: {
          ts: "1", type: "new", tool: "cursor", name: "Old", website: "", github: "",
          category: "", pricing: "", desc: "", email: "old@example.test", x: "",
          found: "", found_other: "", found_flag: "",
        },
      },
    ],
    votes: [
      { key: "votes:2026-w44", expiration: null, value: { day: "2026-10-30", week: { cursor: 2 }, today: { cursor: 1 } } },
    ],
    ...extra,
  };
}

function run(source, now = () => 1_700_000_000_000) {
  const dir = mkdtempSync(join(tmpdir(), "as-cap-"));
  const outPath = join(dir, "blob");
  const key = randomBytes(32);
  try {
    const result = capture(source, { key, now, outPath, startedAt: now() });
    return { dir, outPath, key, result };
  } catch (error) {
    rmSync(dir, { recursive: true, force: true });
    throw error;
  }
}

test("the provider plan is not sendable and rejects a custom statement", () => {
  const plan = planProviderReads();
  assert.equal(plan.executable, false);
  assert.equal(plan.code, "provider_snapshot_unproven");
  assert.equal(plan.requests.length, 2);
  assert.equal(plan.requests.some((item) => /insert|delete|drop/i.test(item.sql)), false);
  assert.throws(() => sendProvider(), (error) => error.code === "remote_disabled");
});

test("a single synthetic response encrypts, restores, and survives a reopen", () => {
  const { dir, outPath, key, result } = run(fixture());
  const dbPath = join(dir, "restore.sqlite");
  try {
    const file = readFileSync(outPath);
    assert.equal(statSync(outPath).mode & 0o777, 0o600);
    assert.equal(file.includes(Buffer.from(EMAIL)), false);
    assert.equal(file.includes(Buffer.from(BODY)), false);
    assert.equal(JSON.stringify(result.manifest).includes(EMAIL), false);
    assert.equal(result.manifest.snapshot_claimed, false);
    assert.equal(result.manifest.provider_snapshot_proven, false);
    assert.equal(result.manifest.submissions_expired_omitted, 1);
    assert.deepEqual(result.manifest.review_statuses, ["pending", "rejected"]);
    restoreBytes(result.encrypted, key, dbPath);
    const counts = reopenCounts(dbPath);
    assert.equal(counts.ratings, 2);
    assert.equal(counts.reviews, 2);
    assert.deepEqual(counts.statuses, ["pending", "rejected"]);
    assert.equal(counts.submissions, 1);
    assert.deepEqual(counts.expiry, [2_000_000_000]);
    assert.equal(counts.votes, 1);
    assert.equal(counts.index, true);
    assert.equal(retentionDue(result.manifest, result.manifest.retain_until - 1), false);
    assert.equal(retentionDue(result.manifest, result.manifest.retain_until), true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("two round trips, writes, truncation, and bad sql write nothing", () => {
  const dir = mkdtempSync(join(tmpdir(), "as-cap-"));
  const outPath = join(dir, "blob");
  const key = randomBytes(32);
  const base = fixture();
  const cases = [
    fixture({ roundTrips: 2 }),
    { ...base, responses: base.responses.map((item) => item.id === "reviews" ? { ...item, rows_written: 1 } : item) },
    { ...base, responses: base.responses.map((item) => item.id === "ratings" ? { ...item, truncated: true } : item) },
    { ...base, responses: base.responses.map((item) => item.id === "ratings" ? { ...item, sql: "DROP TABLE ratings" } : item) },
    { ...base, submissions: [{ key: "rl:vote", expiration: 2_000_000_000, value: base.submissions[0].value }] },
    { ...base, votes: [{ key: "salt:2026-10-30", expiration: null, value: { day: "x", week: {}, today: {} } }] },
    { ...base, submissions: [{ key: "sub:bare", value: base.submissions[0].value }] },
    { ...base, responses: base.responses.map((item) => item.id === "reviews" ? { ...item, rows: item.rows.map((row) => ({ ...row, secret: EMAIL })) } : item) },
  ];
  try {
    for (const source of cases) {
      assert.throws(() => capture(source, { key, outPath, now: () => 1_700_000_000_000 }), (error) => typeof error.code === "string");
      assert.throws(() => readFileSync(outPath));
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a provider error and a tampered blob do not reveal rows", () => {
  const leaking = fixture();
  Object.defineProperty(leaking.responses[1], "rows", {
    get() { throw new Error(`failed near ${EMAIL} ${BODY}`); },
  });
  assert.throws(() => capture(leaking, {
    key: randomBytes(32),
    now: () => 1,
    startedAt: 1,
  }), (error) => error.code === "provider_failed" && !String(error.message).includes(EMAIL) && !String(error.stack).includes(EMAIL));
  const { dir, key, result } = run(fixture());
  const dbPath = join(dir, "nope.sqlite");
  try {
    const blob = Buffer.from(result.encrypted);
    blob[blob.length - 1] ^= 1;
    assert.throws(() => restoreBytes(blob, key, dbPath), (error) => error.code === "tamper");
    assert.throws(() => restoreBytes(result.encrypted, randomBytes(32), dbPath), (error) => error.code === "tamper");
    assert.throws(() => readFileSync(dbPath));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("record, size, and time caps stop before a file exists", () => {
  const now = 1_700_000_000_000;
  const big = fixture();
  big.responses[0].rows = Array.from({ length: 10_001 }, (_, i) => ({
    tool: "cursor", vid: i.toString(16).padStart(4, "0"), iph: "aa", stars: 1, ts: i,
  }));
  assert.throws(() => capture(big, { key: randomBytes(32), now: () => now }), (error) => error.code === "records_cap");
  const wide = fixture();
  wide.responses[1].rows = Array.from({ length: 4200 }, (_, i) => ({
    id: `c${i.toString(16).padStart(4, "0")}`,
    tool: "cursor", vid: "ab", iph: "cd", stars: 3, name: "Ada", body: "x".repeat(8000), status: "pending", ts: i,
  }));
  assert.throws(() => capture(wide, { key: randomBytes(32), now: () => now }), (error) => error.code === "size_cap");
  assert.throws(() => capture(fixture(), {
    key: randomBytes(32),
    now: () => now + 11 * 60 * 1000,
    startedAt: now,
  }), (error) => error.code === "time_cap");
});
