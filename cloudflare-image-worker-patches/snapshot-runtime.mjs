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
    if (url.pathname === "/seed-mixed") {
      // Synthetic only: one rating per tool, reviews in every moderation state.
      this.ctx.storage.transactionSync(() => {
        this.ctx.storage.sql.exec("DELETE FROM reviews");
        this.ctx.storage.sql.exec("DELETE FROM ratings");
        const rows = [["alpha", "va", 5, "approved"], ["beta", "vb", 3, "pending"], ["gamma", "vc", 1, "rejected"]];
        let i = 0;
        for (const [tool, vid, stars, status] of rows) {
          i += 1;
          this.ctx.storage.sql.exec("INSERT INTO ratings (tool, vid, iph, stars, ts) VALUES (?, ?, ?, ?, ?)", tool, vid, "h" + i, stars, 1000 + i);
          this.ctx.storage.sql.exec(
            "INSERT INTO reviews (id, tool, vid, iph, stars, name, body, status, ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            "s" + i, tool, vid, "h" + i, stars, "Synthetic " + i, "synthetic-body-token " + status, status, 2000 + i,
          );
        }
      });
      return new Response("ok");
    }
    if (url.pathname === "/import" && request.method === "POST") {
      // Test-harness restore only. The deployed worker has no import route.
      const snap = await request.json();
      const ratingCols = ["tool", "vid", "iph", "stars", "ts"];
      const reviewCols = ["id", "tool", "vid", "iph", "stars", "name", "body", "status", "ts"];
      const ok = (rows, cols) => Array.isArray(rows) && rows.every((row) => row && cols.every((c) => Object.prototype.hasOwnProperty.call(row, c)) && Object.keys(row).length === cols.length);
      if (!snap || !ok(snap.ratings, ratingCols) || !ok(snap.reviews, reviewCols)) return new Response("bad", { status: 400 });
      const existing = this.ctx.storage.sql.exec("SELECT (SELECT COUNT(*) FROM ratings) + (SELECT COUNT(*) FROM reviews) AS n").one().n;
      if (existing !== 0) return new Response("not_empty", { status: 409 });
      this.ctx.storage.transactionSync(() => {
        for (const r of snap.ratings) this.ctx.storage.sql.exec("INSERT INTO ratings (tool, vid, iph, stars, ts) VALUES (?, ?, ?, ?, ?)", r.tool, r.vid, r.iph, r.stars, r.ts);
        for (const r of snap.reviews) this.ctx.storage.sql.exec("INSERT INTO reviews (id, tool, vid, iph, stars, name, body, status, ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", r.id, r.tool, r.vid, r.iph, r.stars, r.name, r.body, r.status, r.ts);
      });
      return new Response("ok");
    }
    if (url.pathname === "/public") {
      // Mirrors what the public reviews endpoint may show: approved bodies only, counts from ratings.
      const ratings = this.ctx.storage.sql.exec("SELECT tool, COUNT(*) AS n, AVG(stars) AS avg FROM ratings GROUP BY tool ORDER BY tool").toArray();
      const approved = this.ctx.storage.sql.exec("SELECT id FROM reviews WHERE status = 'approved' ORDER BY id").toArray().map((r) => r.id);
      return Response.json({ ratings, approved });
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
