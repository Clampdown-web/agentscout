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
  show({
    score: 10,
    final_url: "https://example.com/",
    listed: { slug: "ok-tool", name: "Ok <b>Tool</b>" },
    checks: [],
  });
  assert.match(out(), /href="\.\.\/tools\/ok-tool\.html"/);
  assert.match(out(), /Ok &lt;b&gt;Tool&lt;\/b&gt;/);
  show({
    score: 10,
    final_url: "https://example.com/",
    listed: { slug: "../<script>", name: "Evil" },
    checks: [],
  });
  assert.equal(out().includes("<script"), false);
  assert.equal(out().includes("../tools/../"), false);
  assert.match(out(), /Not in the AgentScout directory yet/);
});

function bindFns(source, names) {
  const lines = names.map((name) => {
    const line = source.split("\n").find((row) => row.trim().startsWith("const " + name + "="));
    assert.ok(line, name);
    return line.trim();
  });
  return vm.runInNewContext(lines.join("\n") + "; ({ " + names.join(", ") + " })", { URL });
}

test("homepage and app.js only link https URLs, site paths, and local logos", () => {
  const app = readFileSync(new URL("../app.js", import.meta.url), "utf8");
  const { ASsafeLogo: safeLogo, ASsafeHttps: safeHttps, ASsafeIssue: safeIssue } = bindFns(app, ["ASsafeLogo", "ASsafeHttps", "ASsafeIssue"]);
  assert.equal(safeLogo("assets/logos/cursor.png"), "assets/logos/cursor.png");
  assert.equal(safeLogo("https://clampdown-web.github.io/agentscout/assets/logos/cursor.png"), "assets/logos/cursor.png");
  assert.equal(safeLogo("https://evil.example/x.png"), "");
  assert.equal(safeLogo("javascript:alert(1)"), "");
  assert.equal(safeHttps("https://www.theverge.com/ai"), "https://www.theverge.com/ai");
  assert.equal(safeHttps("javascript:alert(1)"), "");
  assert.equal(safeHttps("https://user:pass@agentscouthq.com/"), "");
  assert.equal(safeIssue("https://agentscout.beehiiv.com/p/agentscout-weekly-4-openai-auto-review-10-new-ai-agents"), "https://agentscout.beehiiv.com/p/agentscout-weekly-4-openai-auto-review-10-new-ai-agents");
  assert.equal(safeIssue("javascript:alert(1)"), "");
  assert.equal(safeIssue("https://evil.example/p/post"), "");
  const home = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const { safePage: page, safeHttps: https, safeLogo: logo } = bindFns(home, ["safeHttps", "safePage", "safeLogo"]);
  assert.equal(page("news/2026/11/apple-is-racing-to-make-siri-more-agentic.html"), "news/2026/11/apple-is-racing-to-make-siri-more-agentic.html");
  assert.equal(page("javascript:alert(1)"), "#");
  assert.equal(page("news/../../submit.html"), "#");
  assert.equal(https("https://www.theverge.com/ai-artificial-intelligence/1029552/apple-siri-ai-agentic"), "https://www.theverge.com/ai-artificial-intelligence/1029552/apple-siri-ai-agentic");
  assert.equal(https("javascript:alert(1)"), "#");
  assert.equal(logo("assets/logos/cursor.png"), "assets/logos/cursor.png");
  assert.equal(logo("https://evil.example/logo.png"), "");
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
