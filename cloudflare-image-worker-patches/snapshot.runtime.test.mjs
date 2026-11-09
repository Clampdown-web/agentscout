import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
const { Miniflare } = await import(process.env.MINIFLARE_MODULE || "miniflare");

const TOKEN = "synthetic-body-token";

test("a synchronous snapshot does not split a paired write, and a yielded read can", async () => {
  const persist = mkdtempSync(join(tmpdir(), "as-do-"));
  const mf = new Miniflare({
    modules: true,
    scriptPath: new URL("./snapshot-runtime.mjs", import.meta.url).pathname,
    modulesRules: [{ type: "ESModule", include: ["**/*.js"] }],
    compatibilityDate: "2026-03-01",
    durableObjects: { REVIEWS: { className: "ReviewsDO", useSQLite: true } },
    durableObjectsPersist: persist,
  });
  const fetch = (path) => mf.dispatchFetch("http://example.test" + path);
  let disposed = false;
  try {
    assert.equal((await fetch("/reset")).status, 200);
    const responses = await Promise.all([
      fetch("/snap"),
      fetch("/write-pair?n=1"),
      fetch("/snap"),
      fetch("/write-pair?n=2"),
      fetch("/snap"),
    ]);
    const snaps = [];
    for (const response of responses) {
      const text = await response.text();
      if (text === "ok") continue;
      assert.equal(response.status, 200);
      snaps.push(JSON.parse(text));
    }
    assert.equal(snaps.length, 3);
    for (const snap of snaps) {
      assert.equal(snap.split, false);
      assert.equal(snap.ratings, snap.reviews);
      assert.equal(snap.rows_written, 0);
    }
    assert.equal((await fetch("/reset")).status, 200);
    const pending = fetch("/split-read");
    await new Promise((resolve) => setTimeout(resolve, 15));
    assert.equal((await fetch("/write-pair?n=9")).status, 200);
    const split = await (await pending).json();
    assert.equal(split.split, true);
    assert.equal(split.reviews, split.ratings + 1);

    const raw = await (await fetch("/raw")).text();
    assert.equal(raw.includes(TOKEN), true);
    const plain = Buffer.from(raw);
    const key = randomBytes(32);
    const iv = randomBytes(12);
    assert.throws(() => createCipheriv("aes-256-gcm", Buffer.alloc(16), iv));
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    const sealed = Buffer.concat([cipher.update(plain), cipher.final(), cipher.getAuthTag()]);
    const file = join(tmpdir(), `as-sealed-${process.pid}.bin`);
    const { writeFileSync } = await import("node:fs");
    writeFileSync(file, sealed, { mode: 0o600 });
    assert.equal(readFileSync(file).includes(Buffer.from(TOKEN)), false);
    await mf.dispose();
    disposed = true;

    const restarted = new Miniflare({
      modules: true,
      scriptPath: new URL("./snapshot-runtime.mjs", import.meta.url).pathname,
      modulesRules: [{ type: "ESModule", include: ["**/*.js"] }],
      compatibilityDate: "2026-03-01",
      durableObjects: { REVIEWS: { className: "ReviewsDO", useSQLite: true } },
      durableObjectsPersist: persist,
    });
    try {
      const restored = await (await restarted.dispatchFetch("http://example.test/raw")).text();
      assert.equal(restored, raw);
      const body = readFileSync(file);
      const tag = body.subarray(body.length - 16);
      const open = (bytes, secret) => {
        const decipher = createDecipheriv("aes-256-gcm", secret, iv);
        decipher.setAuthTag(tag);
        return Buffer.concat([decipher.update(bytes), decipher.final()]);
      };
      assert.equal(open(body.subarray(0, body.length - 16), key).toString(), raw);
      const flipped = Buffer.from(body.subarray(0, body.length - 16));
      flipped[0] ^= 1;
      assert.throws(() => open(flipped, key));
      assert.throws(() => open(body.subarray(0, body.length - 16), randomBytes(32)));
    } finally {
      await restarted.dispose();
      rmSync(file, { force: true });
    }
  } finally {
    if (!disposed) await mf.dispose();
    rmSync(persist, { recursive: true, force: true });
  }
});


// Restore drill with synthetic data only: snapshot one Durable Object with the
// deployed reviews-backup.js reader, seal it, then load it into a brand-new
// object with empty storage and check that every row and moderation state
// comes back. No Cloudflare account, binding or network is used.

function runtime(persist) {
  return new Miniflare({
    modules: true,
    scriptPath: new URL("./snapshot-runtime.mjs", import.meta.url).pathname,
    modulesRules: [{ type: "ESModule", include: ["**/*.js"] }],
    compatibilityDate: "2026-03-01",
    durableObjects: { REVIEWS: { className: "ReviewsDO", useSQLite: true } },
    durableObjectsPersist: persist,
    outboundService: () => new Response("blocked", { status: 503 }),
  });
}

function seal(plain, key) {
  const iv = randomBytes(12);
  const c = createCipheriv("aes-256-gcm", key, iv);
  return Buffer.concat([iv, c.update(plain), c.final(), c.getAuthTag()]);
}

function open(blob, key) {
  const iv = blob.subarray(0, 12);
  const tag = blob.subarray(blob.length - 16);
  const d = createDecipheriv("aes-256-gcm", key, iv);
  d.setAuthTag(tag);
  return Buffer.concat([d.update(blob.subarray(12, blob.length - 16)), d.final()]);
}

test("a sealed snapshot restores into a fresh object with every row and status", async () => {
  const source = mkdtempSync(join(tmpdir(), "as-src-"));
  const target = mkdtempSync(join(tmpdir(), "as-dst-"));
  const key = randomBytes(32);
  let sealed;
  let original;
  let originalPublic;
  const a = runtime(source);
  try {
    assert.equal((await a.dispatchFetch("http://x.test/seed-mixed")).status, 200);
    original = await (await a.dispatchFetch("http://x.test/raw")).text();
    originalPublic = await (await a.dispatchFetch("http://x.test/public")).json();
    sealed = seal(Buffer.from(original), key);
    assert.equal(sealed.includes(Buffer.from("synthetic-body-token")), false);
  } finally {
    await a.dispose();
  }

  const b = runtime(target);
  try {
    const empty = JSON.parse(await (await b.dispatchFetch("http://x.test/raw")).text());
    assert.equal(empty.ratings.length + empty.reviews.length, 0);

    const flipped = Buffer.from(sealed);
    flipped[20] ^= 1;
    assert.throws(() => open(flipped, key));
    assert.throws(() => open(sealed, randomBytes(32)));

    const plain = open(sealed, key).toString("utf8");
    const res = await b.dispatchFetch("http://x.test/import", { method: "POST", body: plain });
    assert.equal(res.status, 200);
    const again = await b.dispatchFetch("http://x.test/import", { method: "POST", body: plain });
    assert.equal(again.status, 409);

    const restored = await (await b.dispatchFetch("http://x.test/raw")).text();
    assert.equal(restored, original);
    const snap = JSON.parse(restored);
    assert.deepEqual(snap.reviews.map((r) => r.status).sort(), ["approved", "pending", "rejected"]);
    assert.equal(snap.ratings.length, 3);
    assert.deepEqual(await (await b.dispatchFetch("http://x.test/public")).json(), originalPublic);
    assert.deepEqual(originalPublic.approved, ["s1"]);
  } finally {
    await b.dispose();
  }

  const c = runtime(target);
  try {
    assert.equal(await (await c.dispatchFetch("http://x.test/raw")).text(), original);
  } finally {
    await c.dispose();
    rmSync(source, { recursive: true, force: true });
    rmSync(target, { recursive: true, force: true });
  }
});

test("the restore harness refuses a snapshot with an extra or missing column", async () => {
  const dir = mkdtempSync(join(tmpdir(), "as-bad-"));
  const mf = runtime(dir);
  try {
    const extra = { ratings: [{ tool: "t", vid: "v", iph: "h", stars: 5, ts: 1, email: "x@example.test" }], reviews: [] };
    assert.equal((await mf.dispatchFetch("http://x.test/import", { method: "POST", body: JSON.stringify(extra) })).status, 400);
    const missing = { ratings: [], reviews: [{ id: "r", tool: "t", vid: "v", stars: 5, name: "n", body: "b", status: "pending", ts: 1 }] };
    assert.equal((await mf.dispatchFetch("http://x.test/import", { method: "POST", body: JSON.stringify(missing) })).status, 400);
    const raw = JSON.parse(await (await mf.dispatchFetch("http://x.test/raw")).text());
    assert.equal(raw.ratings.length + raw.reviews.length, 0);
  } finally {
    await mf.dispose();
    rmSync(dir, { recursive: true, force: true });
  }
});
