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
