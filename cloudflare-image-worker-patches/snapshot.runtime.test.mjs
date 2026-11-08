import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createCipheriv, randomBytes } from "node:crypto";
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
    const cipher = createCipheriv("aes-256-gcm", key, iv);
    const sealed = Buffer.concat([cipher.update(plain), cipher.final(), cipher.getAuthTag()]);
    const file = join(persist, "sealed.bin");
    const { writeFileSync } = await import("node:fs");
    writeFileSync(file, sealed, { mode: 0o600 });
    assert.equal(readFileSync(file).includes(Buffer.from(TOKEN)), false);
  } finally {
    await mf.dispose();
    rmSync(persist, { recursive: true, force: true });
  }
});
