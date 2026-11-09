/**
 * Read-only page of the reviews Durable Object. Not a live route until the
 * image worker that exports createBackupDO(ReviewsDO) is deployed on purpose.
 * The response is plaintext JSON for an operator to put in an encrypted archive.
 * This module does not encrypt, and it does not restore anything.
 */
export const EXPORT_PATH = "/reviews/export";
export const BACKUP_LIMIT_MAX = 100;
export const SNAPSHOT_RECORD_CAP = 10000;
export const SNAPSHOT_BYTE_CAP = 32 * 1024 * 1024;
const RATINGS_SQL = "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid";
const REVIEWS_SQL = "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id";
const RATING_COLUMNS = ["tool", "vid", "iph", "stars", "ts"];
const REVIEW_COLUMNS = ["id", "tool", "vid", "iph", "stars", "name", "body", "status", "ts"];

export function exportEnabled(env) {
  return String((env && env.REVIEWS_EXPORT) || "") === "true";
}

export function snapshotEnabled(env) {
  return String((env && env.REVIEWS_SNAPSHOT) || "") === "true";
}

function coded(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

function project(rows, columns) {
  if (!Array.isArray(rows)) throw coded("bad_row");
  return rows.map((row) => {
    if (!row || typeof row !== "object") throw coded("bad_row");
    const copy = {};
    for (const column of columns) {
      if (!Object.prototype.hasOwnProperty.call(row, column)) throw coded("bad_row");
      copy[column] = row[column];
    }
    return copy;
  });
}

/**
 * Read ratings and reviews inside one synchronous storage transaction.
 * There is no HTTP route. REVIEWS_SNAPSHOT must be the string "true" before
 * the class method will call this, and that flag is not set in this repo.
 * Workers KV is not readable here and is not part of the result.
 */
export function readConsistentSnapshot(storage) {
  if (!storage || typeof storage.transactionSync !== "function" || !storage.sql || typeof storage.sql.exec !== "function") {
    throw coded("snapshot_unavailable");
  }
  let result;
  try {
    result = storage.transactionSync(() => {
      const ratingsCursor = storage.sql.exec(RATINGS_SQL);
      const reviewsCursor = storage.sql.exec(REVIEWS_SQL);
      if (typeof ratingsCursor.toArray !== "function" || typeof reviewsCursor.toArray !== "function") throw coded("snapshot_unavailable");
      const ratings = project(ratingsCursor.toArray(), RATING_COLUMNS);
      const reviews = project(reviewsCursor.toArray(), REVIEW_COLUMNS);
      const written = ratingsCursor.rowsWritten + reviewsCursor.rowsWritten;
      if (written !== 0) throw coded("rows_written");
      if (ratings.length + reviews.length > SNAPSHOT_RECORD_CAP) throw coded("records_cap");
      if (JSON.stringify({ ratings, reviews }).length > SNAPSHOT_BYTE_CAP) throw coded("size_cap");
      return { ratings, reviews, rows_written: 0 };
    });
  } catch (error) {
    if (error && error.code && error.message === error.code) throw error;
    throw coded("snapshot_failed");
  }
  if (!result || typeof result.then === "function") throw coded("snapshot_unavailable");
  return result;
}

const TABLES = {
  ratings: {
    columns: ["tool", "vid", "iph", "stars", "ts"],
    sql: "SELECT tool, vid, iph, stars, ts FROM ratings WHERE (tool > ? OR (tool = ? AND vid > ?)) ORDER BY tool, vid LIMIT ?",
    empty: { tool: "", vid: "" },
    valid(cursor) {
      return !!cursor && typeof cursor.tool === "string" && typeof cursor.vid === "string"
        && Object.keys(cursor).length === 2
        && /^[a-z0-9-]{0,100}$/.test(cursor.tool)
        && /^[a-f0-9]{0,64}$/.test(cursor.vid);
    },
    bind(cursor, limit) {
      return [cursor.tool, cursor.tool, cursor.vid, limit];
    },
    next(row) {
      return { tool: row.tool, vid: row.vid };
    },
  },
  reviews: {
    columns: ["id", "tool", "vid", "iph", "stars", "name", "body", "status", "ts"],
    sql: "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews WHERE id > ? ORDER BY id LIMIT ?",
    empty: { id: "" },
    valid(cursor) {
      return !!cursor && typeof cursor.id === "string" && Object.keys(cursor).length === 1
        && /^[0-9a-f-]{0,36}$/.test(cursor.id);
    },
    bind(cursor, limit) {
      return [cursor.id, limit];
    },
    next(row) {
      return { id: row.id };
    },
  },
  limits: {
    columns: ["k", "n", "exp"],
    sql: "SELECT k, n, exp FROM limits WHERE k > ? ORDER BY k LIMIT ?",
    empty: { k: "" },
    valid(cursor) {
      return !!cursor && typeof cursor.k === "string" && Object.keys(cursor).length === 1
        && /^[A-Za-z0-9:._|-]{0,160}$/.test(cursor.k);
    },
    bind(cursor, limit) {
      return [cursor.k, limit];
    },
    next(row) {
      return { k: row.k };
    },
  },
};

function exportJson(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "private, no-store",
      "cdn-cache-control": "no-store",
      "x-content-type-options": "nosniff",
      "x-frame-options": "DENY",
      "referrer-policy": "strict-origin-when-cross-origin",
      "strict-transport-security": "max-age=31536000; includeSubDomains",
      "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
      "x-robots-tag": "noindex",
    },
  });
}

function encodeCursor(obj) {
  const bytes = new TextEncoder().encode(JSON.stringify(obj));
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function decodeCursor(table, raw) {
  if (!raw) return { value: TABLES[table].empty };
  if (!/^[A-Za-z0-9_-]{1,400}$/.test(raw)) return { error: "Bad cursor." };
  try {
    const padded = raw.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((raw.length + 3) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const parsed = JSON.parse(new TextDecoder().decode(bytes));
    if (!TABLES[table].valid(parsed)) return { error: "Bad cursor." };
    return { value: parsed };
  } catch {
    return { error: "Bad cursor." };
  }
}

export function parseBackupRequest(url) {
  const table = url.searchParams.get("table") || "";
  if (!Object.prototype.hasOwnProperty.call(TABLES, table)) return { error: "Unknown table." };
  const limitRaw = url.searchParams.get("limit");
  let limit = BACKUP_LIMIT_MAX;
  if (limitRaw != null && limitRaw !== "") {
    if (!/^\d{1,3}$/.test(limitRaw)) return { error: "Bad limit." };
    limit = Number(limitRaw);
    if (limit < 1 || limit > BACKUP_LIMIT_MAX) return { error: "Bad limit." };
  }
  const cursor = decodeCursor(table, url.searchParams.get("cursor") || "");
  if (cursor.error) return cursor;
  return { table, limit, cursor: cursor.value };
}

export function readBackupPage(sql, spec) {
  const table = TABLES[spec && spec.table];
  if (!table) throw new Error("bad table");
  if (!Number.isInteger(spec.limit) || spec.limit < 1 || spec.limit > BACKUP_LIMIT_MAX) throw new Error("bad limit");
  const cursor = spec.cursor && Object.keys(spec.cursor).length ? spec.cursor : table.empty;
  if (!table.valid(cursor)) throw new Error("bad cursor");
  if (!sql || typeof sql.exec !== "function") throw new Error("backup unavailable");
  const rows = sql.exec(table.sql, ...table.bind(cursor, spec.limit)).toArray().map((row) => {
    const copy = {};
    for (const column of table.columns) copy[column] = row[column] ?? null;
    return copy;
  });
  const next = rows.length === spec.limit ? encodeCursor(table.next(rows[rows.length - 1])) : null;
  return { table: spec.table, rows, next };
}

export function createBackupDO(Base) {
  return class ReviewsDO extends Base {
    async backupPage(spec) {
      return readBackupPage(this.sql, spec);
    }

    snapshotRatingsReviews() {
      if (!snapshotEnabled(this.env)) throw coded("snapshot_disabled");
      return readConsistentSnapshot(this.ctx && this.ctx.storage);
    }
  };
}

export async function handleReviewsExport(request, env) {
  let url;
  try {
    url = new URL(request.url);
  } catch {
    return exportJson({ error: "Bad request." }, 400);
  }
  if (request.method !== "GET") return exportJson({ error: "Use GET." }, 405);
  const parsed = parseBackupRequest(url);
  if (parsed.error) return exportJson({ error: parsed.error }, 400);
  const ns = env && env.REVIEWS;
  if (!ns || typeof ns.get !== "function" || typeof ns.idFromName !== "function") {
    return exportJson({ error: "Export is not available." }, 503);
  }
  try {
    const stub = ns.get(ns.idFromName("all"));
    if (!stub || typeof stub.backupPage !== "function") return exportJson({ error: "Export is not available." }, 503);
    const page = await stub.backupPage({ table: parsed.table, limit: parsed.limit, cursor: parsed.cursor });
    if (!page || !Array.isArray(page.rows)) return exportJson({ error: "Export failed." }, 500);
    return exportJson({ table: parsed.table, rows: page.rows, next: page.next || null }, 200);
  } catch {
    return exportJson({ error: "Export failed." }, 500);
  }
}
