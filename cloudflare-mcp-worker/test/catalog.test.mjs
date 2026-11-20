import test from "node:test";
import assert from "node:assert/strict";
import { catalogFromApi } from "../worker.js";

test("a published api/tools.json row becomes a get_tool record", () => {
  const view = catalogFromApi({
    updated: "2026-11-19T16:00:21Z",
    last_checked: "2026-11-19",
    tools: [
      {
        name: "BeatMV",
        slug: "beatmv",
        category: "MCP servers",
        description: "A music MCP server.",
        pricing: "Free",
        price_tag: "free",
        open_source: true,
        tags: [],
        platforms: ["Developer (API/SDK)"],
        page: "https://agentscouthq.com/tools/beatmv.html",
      },
    ],
  });
  assert.equal(view.bySlug.get("beatmv").name, "BeatMV");
  assert.equal(view.count, 1);
  assert.equal(view.mcp_count, 1);
  assert.equal(view.last_checked, "2026-11-19");
  assert.match(view.updated, /^2026-11-19T08:00:21-08:00$/);
  assert.equal(view.updated.endsWith("Z"), false);
});

test("an empty fetch is not a catalog", () => {
  const view = catalogFromApi({ tools: [] });
  assert.equal(view.count, 0);
});
