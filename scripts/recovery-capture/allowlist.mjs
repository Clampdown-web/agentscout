/** Fixed read shapes. Callers cannot pass SQL. */

export const LIMITS = {
  records: 10_000,
  bytes: 32 * 1024 * 1024,
  ms: 10 * 60 * 1000,
  retainMs: 7 * 24 * 60 * 60 * 1000,
};

export const DO_QUERIES = [
  {
    id: "ratings",
    sql: "SELECT tool, vid, iph, stars, ts FROM ratings ORDER BY tool, vid",
    columns: ["tool", "vid", "iph", "stars", "ts"],
  },
  {
    id: "reviews",
    sql: "SELECT id, tool, vid, iph, stars, name, body, status, ts FROM reviews ORDER BY id",
    columns: ["id", "tool", "vid", "iph", "stars", "name", "body", "status", "ts"],
  },
];

const BY_ID = new Map(DO_QUERIES.map((query) => [query.id, query]));

export function queryById(id) {
  const query = BY_ID.get(id);
  if (!query) {
    const error = new Error("sql_rejected");
    error.code = "sql_rejected";
    throw error;
  }
  return query;
}

/** The published OpenAPI file checked on 2026-11-08 does not define this body. */
export function planProviderReads() {
  return {
    executable: false,
    code: "provider_snapshot_unproven",
    permission: "Workers Scripts Write is documented for Data Studio and is not checked here",
    requests: DO_QUERIES.map((query) => ({
      method: "POST",
      path: "/accounts/{account_id}/workers/durable_objects/namespaces/{namespace_id}/query/v2",
      sql: query.sql,
      params: [],
    })),
  };
}

export function sendProvider() {
  const error = new Error("remote_disabled");
  error.code = "remote_disabled";
  throw error;
}
