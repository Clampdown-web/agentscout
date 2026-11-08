import { DatabaseSync } from "node:sqlite";
import { decryptBytes } from "./crypto.mjs";

function openDb(path) {
  const db = new DatabaseSync(path);
  db.exec(`
    CREATE TABLE IF NOT EXISTS ratings (
      tool TEXT NOT NULL,
      vid TEXT NOT NULL,
      iph TEXT,
      stars INTEGER NOT NULL,
      ts INTEGER NOT NULL,
      PRIMARY KEY (tool, vid)
    );
    CREATE TABLE IF NOT EXISTS reviews (
      id TEXT PRIMARY KEY,
      tool TEXT NOT NULL,
      vid TEXT NOT NULL,
      iph TEXT,
      stars INTEGER NOT NULL,
      name TEXT NOT NULL,
      body TEXT NOT NULL,
      status TEXT NOT NULL,
      ts INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS reviews_status ON reviews(status);
    CREATE TABLE IF NOT EXISTS submissions (
      key TEXT PRIMARY KEY,
      expiration INTEGER NOT NULL,
      value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS votes (
      key TEXT PRIMARY KEY,
      expiration INTEGER,
      value TEXT NOT NULL
    );
  `);
  return db;
}

export function restoreBytes(blob, key, dbPath) {
  const payload = JSON.parse(decryptBytes(blob, key).toString("utf8"));
  if (payload.snapshot_claimed !== false || payload.provider_snapshot_proven !== false) {
    const error = new Error("tamper");
    error.code = "tamper";
    throw error;
  }
  const db = openDb(dbPath);
  const insertRating = db.prepare("INSERT INTO ratings (tool, vid, iph, stars, ts) VALUES (?, ?, ?, ?, ?)");
  const insertReview = db.prepare("INSERT INTO reviews (id, tool, vid, iph, stars, name, body, status, ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
  const insertSub = db.prepare("INSERT INTO submissions (key, expiration, value) VALUES (?, ?, ?)");
  const insertVote = db.prepare("INSERT INTO votes (key, expiration, value) VALUES (?, ?, ?)");
  for (const row of payload.ratings) insertRating.run(row.tool, row.vid, row.iph, row.stars, row.ts);
  for (const row of payload.reviews) insertReview.run(row.id, row.tool, row.vid, row.iph, row.stars, row.name, row.body, row.status, row.ts);
  for (const row of payload.submissions) insertSub.run(row.key, row.expiration, JSON.stringify(row.value));
  for (const row of payload.votes) insertVote.run(row.key, row.expiration, JSON.stringify(row.value));
  db.close();
  return { ratings: payload.ratings.length, reviews: payload.reviews.length, retain_until: payload.retain_until };
}

export function reopenCounts(dbPath) {
  const db = new DatabaseSync(dbPath);
  const count = (table) => db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).get().n;
  const statuses = db.prepare("SELECT status FROM reviews ORDER BY status").all().map((row) => row.status);
  const index = db.prepare("SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'reviews_status'").get();
  const expiry = db.prepare("SELECT expiration FROM submissions ORDER BY key").all().map((row) => row.expiration);
  const counts = { ratings: count("ratings"), reviews: count("reviews"), submissions: count("submissions"), votes: count("votes"), statuses, index: !!(index && index.name), expiry };
  db.close();
  return counts;
}
