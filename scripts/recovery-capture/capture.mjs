import { writeFileSync } from "node:fs";
import { DO_QUERIES, LIMITS, queryById } from "./allowlist.mjs";
import { encryptBytes } from "./crypto.mjs";

const SUB_KEYS = ["ts", "type", "tool", "name", "website", "github", "category", "pricing", "desc", "email", "x", "found", "found_other", "found_flag"];

function fail(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

function str(value, max) {
  return typeof value === "string" && value.length <= max;
}

function copyRow(spec, row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) throw fail("bad_row");
  const keys = Object.keys(row);
  if (keys.length !== spec.columns.length || spec.columns.some((column) => !keys.includes(column))) throw fail("bad_row");
  const copy = {};
  for (const column of spec.columns) copy[column] = row[column];
  if (spec.id === "ratings") {
    if (!str(copy.tool, 100) || !/^[a-z0-9-]{1,100}$/.test(copy.tool)) throw fail("bad_row");
    if (!str(copy.vid, 64) || !/^[a-f0-9]{1,64}$/.test(copy.vid)) throw fail("bad_row");
    if (!str(copy.iph, 64) || !/^[a-f0-9]{0,64}$/.test(copy.iph)) throw fail("bad_row");
    if (!Number.isInteger(copy.stars) || copy.stars < 1 || copy.stars > 5) throw fail("bad_row");
    if (!Number.isInteger(copy.ts)) throw fail("bad_row");
  }
  if (spec.id === "reviews") {
    if (!str(copy.id, 36) || !/^[0-9a-f-]{1,36}$/.test(copy.id)) throw fail("bad_row");
    if (!str(copy.tool, 100) || !str(copy.vid, 64) || !str(copy.iph, 64)) throw fail("bad_row");
    if (!str(copy.name, 200) || !str(copy.body, 8000)) throw fail("bad_row");
    if (!str(copy.status, 32) || !/^[a-z]{1,32}$/.test(copy.status)) throw fail("bad_row");
    if (!Number.isInteger(copy.stars) || copy.stars < 1 || copy.stars > 5) throw fail("bad_row");
    if (!Number.isInteger(copy.ts)) throw fail("bad_row");
  }
  return copy;
}

function takeQuery(source, spec) {
  const found = (source.responses || []).filter((item) => item && item.id === spec.id);
  if (found.length !== 1) throw fail("sql_rejected");
  const response = found[0];
  if (response.sql != null && response.sql !== spec.sql) throw fail("sql_rejected");
  if (response.rows_written !== 0) throw fail("rows_written");
  if (response.truncated || response.cursor) throw fail("incomplete");
  if (!Array.isArray(response.rows)) throw fail("bad_row");
  return response.rows.map((row) => copyRow(spec, row));
}

function submission(entry, nowSec) {
  if (!entry || typeof entry.key !== "string" || !/^sub:[A-Za-z0-9:_-]{1,200}$/.test(entry.key)) throw fail("submission_key");
  if (!Number.isInteger(entry.expiration)) throw fail("submission_expiry");
  if (entry.expiration <= nowSec) return null;
  const value = entry.value;
  if (!value || typeof value !== "object" || Array.isArray(value)) throw fail("bad_row");
  const keys = Object.keys(value);
  if (keys.length !== SUB_KEYS.length || SUB_KEYS.some((key) => !keys.includes(key))) throw fail("bad_row");
  const copy = {};
  for (const key of SUB_KEYS) {
    if (!str(value[key], 4000)) throw fail("bad_row");
    copy[key] = value[key];
  }
  return { key: entry.key, expiration: entry.expiration, value: copy };
}

function vote(entry, nowSec) {
  if (!entry || typeof entry.key !== "string" || !/^votes:\d{4}-w\d{2}$/.test(entry.key)) throw fail("votes_key");
  if (entry.expiration != null && !Number.isInteger(entry.expiration)) throw fail("bad_row");
  if (Number.isInteger(entry.expiration) && entry.expiration <= nowSec) return null;
  const value = entry.value;
  if (!value || typeof value !== "object" || typeof value.day !== "string") throw fail("bad_row");
  for (const part of ["week", "today"]) {
    const map = value[part];
    if (!map || typeof map !== "object" || Array.isArray(map)) throw fail("bad_row");
    for (const count of Object.values(map)) {
      if (!Number.isInteger(count) || count < 0) throw fail("bad_row");
    }
  }
  if (Object.keys(value).some((key) => !["day", "week", "today"].includes(key))) throw fail("bad_row");
  return {
    key: entry.key,
    expiration: entry.expiration ?? null,
    value: { day: value.day, week: { ...value.week }, today: { ...value.today } },
  };
}

function publicView(payload) {
  return {
    records: payload.ratings.length + payload.reviews.length + payload.submissions.length + payload.votes.length,
    ratings: payload.ratings.length,
    reviews: payload.reviews.length,
    review_statuses: [...new Set(payload.reviews.map((row) => row.status))].sort(),
    submissions: payload.submissions.length,
    submissions_expired_omitted: payload.submissions_expired_omitted,
    votes: payload.votes.length,
    snapshot_claimed: false,
    provider_snapshot_proven: false,
    fixture_round_trips: payload.round_trips,
    consistency: "separate-requests-unless-a-single-fixture-response",
    captured_at: payload.captured_at,
    retain_until: payload.retain_until,
    bytes: payload.bytes,
  };
}

export function retentionDue(manifest, nowMs) {
  return nowMs >= manifest.retain_until;
}

/**
 * Encrypt one synthetic fixture. Refuses multi-request input and never calls a network.
 * The manifest says the provider snapshot is unproven even when the fixture was one response.
 */
export function capture(source, options) {
  const now = options.now || (() => Date.now());
  const started = options.startedAt ?? now();
  try {
    if (!source || source.roundTrips !== 1) throw fail("not_a_snapshot");
    if (!Array.isArray(source.responses) || source.responses.length !== DO_QUERIES.length) throw fail("not_a_snapshot");
    const ratings = takeQuery(source, queryById("ratings"));
    const reviews = takeQuery(source, queryById("reviews"));
    const nowSec = Math.floor(now() / 1000);
    let submissionsExpired = 0;
    const submissions = [];
    for (const entry of source.submissions || []) {
      const kept = submission(entry, nowSec);
      if (!kept) submissionsExpired += 1;
      else submissions.push(kept);
    }
    const votes = [];
    for (const entry of source.votes || []) {
      const kept = vote(entry, nowSec);
      if (kept) votes.push(kept);
    }
    const records = ratings.length + reviews.length + submissions.length + votes.length;
    if (records > LIMITS.records) throw fail("records_cap");
    const finished = now();
    if (finished - started > LIMITS.ms) throw fail("time_cap");
    const capturedAt = finished;
    const payload = {
      ratings,
      reviews,
      submissions,
      submissions_expired_omitted: submissionsExpired,
      votes,
      round_trips: 1,
      captured_at: capturedAt,
      retain_until: capturedAt + LIMITS.retainMs,
      snapshot_claimed: false,
      provider_snapshot_proven: false,
    };
    const plain = Buffer.from(JSON.stringify(payload));
    if (plain.length > LIMITS.bytes) throw fail("size_cap");
    payload.bytes = plain.length;
    const encrypted = encryptBytes(Buffer.from(JSON.stringify(payload)), options.key);
    if (options.outPath) writeFileSync(options.outPath, encrypted, { mode: 0o600 });
    return { manifest: publicView(payload), encrypted };
  } catch (error) {
    if (error && error.code && error.message === error.code) throw error;
    throw fail("provider_failed");
  }
}
