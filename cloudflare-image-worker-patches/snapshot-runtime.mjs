import { DurableObject } from "cloudflare:workers";
import { readConsistentSnapshot } from "./reviews-backup.js";

export class ReviewsDO extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => {
      ctx.storage.sql.exec(`
        CREATE TABLE IF NOT EXISTS ratings (
          tool TEXT NOT NULL, vid TEXT NOT NULL, iph TEXT, stars INTEGER NOT NULL, ts INTEGER NOT NULL,
          PRIMARY KEY (tool, vid)
        );
        CREATE TABLE IF NOT EXISTS reviews (
          id TEXT PRIMARY KEY, tool TEXT NOT NULL, vid TEXT NOT NULL, iph TEXT,
          stars INTEGER NOT NULL, name TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL, ts INTEGER NOT NULL
        );
      `);
    });
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/reset") {
      this.ctx.storage.sql.exec("DELETE FROM reviews");
      this.ctx.storage.sql.exec("DELETE FROM ratings");
      this.ctx.storage.sql.exec("INSERT INTO ratings (tool, vid, iph, stars, ts) VALUES ('cursor', 'aa', 'bb', 5, 1)");
      this.ctx.storage.sql.exec("INSERT INTO reviews (id, tool, vid, iph, stars, name, body, status, ts) VALUES ('r1', 'cursor', 'aa', 'bb', 5, 'A', 'synthetic-body-token', 'pending', 1)");
      return new Response("ok");
    }
    if (url.pathname === "/write-pair") {
      const n = url.searchParams.get("n") || "1";
      this.ctx.storage.transactionSync(() => {
        this.ctx.storage.sql.exec("INSERT INTO ratings (tool, vid, iph, stars, ts) VALUES (?, ?, 'dd', 4, 2)", "t" + n, "v" + n);
        this.ctx.storage.sql.exec("INSERT INTO reviews (id, tool, vid, iph, stars, name, body, status, ts) VALUES (?, ?, ?, 'dd', 4, 'B', 'two', 'rejected', 2)", "id" + n, "t" + n, "v" + n);
      });
      return new Response("ok");
    }
    if (url.pathname === "/raw") {
      return Response.json(readConsistentSnapshot(this.ctx.storage));
    }
    if (url.pathname === "/snap") {
      const snap = readConsistentSnapshot(this.ctx.storage);
      const tools = new Set(snap.ratings.map((row) => row.tool));
      const split = snap.reviews.some((row) => !tools.has(row.tool));
      return Response.json({ ratings: snap.ratings.length, reviews: snap.reviews.length, split, rows_written: snap.rows_written });
    }
    if (url.pathname === "/split-read") {
      const ratings = this.ctx.storage.sql.exec("SELECT tool FROM ratings").toArray();
      await scheduler.wait(40);
      const reviews = this.ctx.storage.sql.exec("SELECT tool FROM reviews").toArray();
      const tools = new Set(ratings.map((row) => row.tool));
      const split = reviews.some((row) => !tools.has(row.tool));
      return Response.json({ ratings: ratings.length, reviews: reviews.length, split });
    }
    return new Response("no", { status: 404 });
  }
}

export default {
  async fetch(request, env) {
    const stub = env.REVIEWS.get(env.REVIEWS.idFromName("all"));
    return stub.fetch(request);
  },
};
