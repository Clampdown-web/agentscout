import test from "node:test";
import assert from "node:assert/strict";
import { allowOrigin, parseSlugs, normalizeStored, castInDoc, countsFor, isoWeek } from "../src/worker.js";

test("cors allowlist is the site and www only", () => {
  assert.equal(allowOrigin("https://agentscouthq.com"), "https://agentscouthq.com");
  assert.equal(allowOrigin("https://www.agentscouthq.com"), "https://www.agentscouthq.com");
  assert.equal(allowOrigin("https://evil.example"), "");
  assert.equal(allowOrigin("https://agentscouthq.com.evil"), "");
  assert.equal(allowOrigin(""), "");
});

test("iso week key matches the Pacific date's ISO week", () => {
  assert.equal(isoWeek("2026-10-30"), "2026-w44");
  assert.equal(isoWeek("2026-10-26"), "2026-w44");
  assert.equal(isoWeek("2026-11-02"), "2026-w45");
});

test("slug list is unique and capped at 400", () => {
  const raw = Array.from({ length: 450 }, (_, i) => `tool-${i}`).join(",");
  const slugs = parseSlugs(raw + ",tool-1,not a slug");
  assert.equal(slugs.length, 400);
  assert.equal(slugs[0], "tool-0");
  assert.equal(slugs.includes("not"), false);
});

test("week document is one map, and today resets when the day changes", () => {
  const stored = normalizeStored({ day: "2026-10-30", week: { sickle: 3 }, today: { sickle: 1 } }, "2026-10-30");
  assert.equal(stored.week.sickle, 3);
  assert.equal(stored.today.sickle, 1);
  const nextDay = normalizeStored({ day: "2026-10-30", week: { sickle: 3 }, today: { sickle: 1 } }, "2026-10-31");
  assert.equal(nextDay.day, "");
  assert.equal(nextDay.week.sickle, 3);
  assert.deepEqual(nextDay.today, {});
  const voted = castInDoc(nextDay, "sickle", "2026-10-31");
  assert.equal(voted.week.sickle, 4);
  assert.equal(voted.today.sickle, 1);
  assert.equal(voted.day, "2026-10-31");
  const again = castInDoc(voted, "other-tool", "2026-10-31");
  assert.equal(again.week.sickle, 4);
  assert.equal(again.week["other-tool"], 1);
  assert.equal(again.today.sickle, 1);
});

test("public counts omit the visitor flag", () => {
  const doc = castInDoc(normalizeStored(null, "2026-10-30"), "sickle", "2026-10-30");
  const counts = countsFor(doc, ["sickle", "missing"], "2026-10-30");
  assert.deepEqual(counts.tools.sickle, { votes: 1, today: 1 });
  assert.equal("yours" in counts.tools.sickle, false);
  assert.equal(counts.tools.missing.votes, 0);
  assert.equal(counts.today_total, 1);
});
