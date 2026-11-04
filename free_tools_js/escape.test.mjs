import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

function load(file) {
  const elements = {};
  function element(id) {
    if (!elements[id]) {
      elements[id] = {
        value: "",
        addEventListener() {},
        requestSubmit() {},
        setAttribute() {},
      };
    }
    return elements[id];
  }
  const context = vm.createContext({
    document: { getElementById: element },
    location: { hash: "" },
    history: { replaceState() {} },
    fetch() { return Promise.reject(new Error("offline")); },
    console,
  });
  vm.runInContext(readFileSync(new URL(file, import.meta.url), "utf8"), context);
  return { show: context.show, out: () => element("rout").innerHTML || "" };
}

test("roast.js escapes score and points before innerHTML", () => {
  const { show, out } = load("./roast.js");
  show({
    score: "<img src=x onerror=alert(1)>",
    final_url: "https://example.com/?q=<script>",
    checks: [{ ok: false, label: "<b>Title</b>", points: "<svg onload=alert(1)>", fix: "<i>fix</i>" }],
  });
  const html = out();
  assert.equal(html.includes("<img"), false);
  assert.equal(html.includes("<svg"), false);
  assert.equal(html.includes("<script"), false);
  assert.equal(html.includes("onerror"), false);
  assert.equal(html.includes("onload"), false);
  assert.match(html, /&lt;b&gt;Title/);
  assert.match(html, /&lt;script&gt;/);
  show({ score: 81, final_url: "https://example.com/", checks: [{ ok: true, label: "Title", points: 12 }] });
  assert.match(out(), /81\/100/);
  assert.match(out(), /12 pts/);
});

test("readiness.js escapes status, link count, and text length before innerHTML", () => {
  const { show, out } = load("./readiness.js");
  show({
    reachable: true,
    site: "https://example.com/<script>",
    checked: "2026-11-04T00:00:00Z",
    cached: false,
    home: {
      status: "<img src=x onerror=alert(1)>",
      https: false,
      title: "Example",
      description: "A site",
      json_ld: false,
      open_graph: false,
      text_chars: { valueOf() { return 12; }, toLocaleString() { return "<svg onload=alert(1)>"; } },
      noindex: false,
    },
    llms_txt: { found: true, has_title: true, links: "<script>alert(1)</script>" },
    robots: { found: true, ai_bots_blocked: {}, sitemap_listed: true },
    sitemap: { found: true },
    mcp_json: { found: false },
    agent_card: { found: false },
    ai_plugin: { found: false },
    openapi: { found: false },
  });
  const html = out();
  assert.doesNotMatch(html, /<img|<svg|<script/);
  assert.match(html, /&lt;script&gt;/);
  show({
    reachable: true,
    site: "https://example.com/",
    checked: "2026-11-04T00:00:00Z",
    home: {
      status: 200,
      https: true,
      title: "Example",
      description: "A site",
      json_ld: true,
      open_graph: true,
      text_chars: 1200,
      noindex: false,
    },
    llms_txt: { found: true, has_title: true, links: 4 },
    robots: { found: true, ai_bots_blocked: {}, sitemap_listed: true },
    sitemap: { found: true },
    mcp_json: { found: false },
    agent_card: { found: false },
    ai_plugin: { found: false },
    openapi: { found: false },
  });
  assert.match(out(), /1,200 characters|1200 characters/);
  assert.match(out(), /4 links/);
  assert.match(out(), /100/);
});
