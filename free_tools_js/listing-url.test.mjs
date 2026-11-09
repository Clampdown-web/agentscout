import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

function element(id, extra) {
  const el = {
    id,
    value: "",
    hidden: false,
    dataset: extra && extra.dataset || {},
    classList: { add() {}, toggle() {}, contains() { return false; } },
    style: {},
    addEventListener() {},
    setAttribute() {},
    getAttribute(name) { return name === "data-pairs" ? (this.dataset.pairs || "") : ""; },
    appendChild() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
    ...extra,
  };
  return el;
}

function load(file, context) {
  context.URL = URL;
  context.URLSearchParams = URLSearchParams;
  context.Promise = Promise;
  context.window = context;
  vm.runInContext(readFileSync(new URL(file, import.meta.url), "utf8"), context);
  return context;
}

test("listing links keep https tool URLs and drop scriptable schemes", () => {
  const context = vm.createContext({
    document: { getElementById() { return null; } },
    console,
  });
  load("../compare-picker.js", context);
  const site = "https://cursor.com/pricing";
  assert.equal(context.asListingHttp(site), site);
  assert.equal(context.asListingHttp(" http://example.com/a "), "http://example.com/a");
  assert.equal(context.asListingHttp("javascript:alert(1)"), "");
  assert.equal(context.asListingHttp("data:text/html,hi"), "");
  assert.equal(context.asListingHttp("https://user:pass@example.com/"), "");
  assert.equal(context.asListingHttp("https://agentscouthq.com.evil/"), "https://agentscouthq.com.evil/");
  const logo = "https://agentscouthq.com/assets/logos/cursor.png";
  assert.equal(context.asListingLogo(logo), logo);
  assert.equal(context.asListingLogo("https://www.agentscouthq.com/assets/logos/cursor.png"), "https://www.agentscouthq.com/assets/logos/cursor.png");
  assert.equal(context.asListingLogo("https://evil.example/assets/logos/cursor.png"), "");
  assert.equal(context.asListingLogo("javascript:alert(1)"), "");
  assert.equal(context.asListingLogo("assets/logos/cursor.png"), "assets/logos/cursor.png");
  assert.equal(context.asSlug("cursor"), "cursor");
  assert.equal(context.asSlug("cursor\"><script>"), "");
});

test("compare table does not put a javascript website into href", async () => {
  const els = {};
  function make(id, extra) {
    if (!els[id]) els[id] = element(id, extra);
    return els[id];
  }
  make("cpick", { dataset: { pairs: "cursor-vs-windsurf" } });
  make("cp-res");
  make("cp-a");
  make("cp-a-l");
  make("cp-b");
  make("cp-b-l");
  make("cp-go");
  make("cp-swap");
  make("cp-copy");
  const tools = [
    {
      name: "Bad <b>",
      slug: "bad-tool",
      category: "coding",
      pricing: "Free",
      description: "x",
      website: "javascript:alert(1)",
      github: "https://github.com/example/bad",
      logo: "https://evil.example/x.png",
    },
    {
      name: "Cursor",
      slug: "cursor",
      category: "coding",
      pricing: "Free",
      description: "Editor",
      website: "https://cursor.com/",
      github: "https://github.com/getcursor/cursor",
      logo: "https://agentscouthq.com/assets/logos/cursor.png",
    },
  ];
  const context = vm.createContext({
    document: { getElementById: make },
    location: { pathname: "/compare/index.html", search: "?a=bad-tool&b=cursor", origin: "https://agentscouthq.com" },
    history: { replaceState() {} },
    fetch() { return Promise.resolve({ json: async () => tools }); },
    AS: { saveBtn(slug) { return `<button class="save" data-save="${slug}"></button>`; } },
    console,
  });
  load("../compare-picker.js", context);
  await new Promise((resolve) => setTimeout(resolve, 0));
  const html = els["cp-res"].innerHTML || "";
  assert.equal(html.includes("javascript:"), false);
  assert.equal(html.includes("evil.example"), false);
  assert.match(html, /href="https:\/\/cursor\.com\/"/);
  assert.match(html, /href="https:\/\/github\.com\/example\/bad"/);
  assert.match(html, /src="https:\/\/agentscouthq\.com\/assets\/logos\/cursor\.png"/);
  assert.match(html, /data-save="cursor"/);
  assert.match(html, /&lt;b&gt;/);
});

test("tool cards and generator art keep the live catalog values", () => {
  const context = vm.createContext({
    document: {
      readyState: "loading",
      addEventListener() {},
      querySelector() { return null; },
      querySelectorAll() { return []; },
      getElementById() { return null; },
      documentElement: { style: { setProperty() {} } },
      body: null,
    },
    location: { pathname: "/", search: "", href: "https://agentscouthq.com/", hash: "" },
    history: { replaceState() {} },
    localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} },
    sessionStorage: { getItem() { return null; }, setItem() {} },
    navigator: {},
    fetch() { return Promise.reject(new Error("offline")); },
    matchMedia() { return { matches: false, addEventListener() {} }; },
    MutationObserver: class { observe() {} },
    ResizeObserver: class { observe() {} },
    PerformanceObserver: class { observe() {} },
    requestIdleCallback(fn) { fn(); },
    CSS: { escape(s) { return s; } },
    Intl,
    console,
    addEventListener() {},
  });
  context.window = context;
  load("../app.js", context);
  function cardFor(tool) {
    return vm.runInContext(`AS.card(${JSON.stringify(tool)})`, context);
  }
  const card = cardFor({
    name: "Cursor",
    slug: "cursor",
    category: "coding",
    pricing: "Free",
    description: "Editor",
    added: "2020-01-01",
    logo: "https://agentscouthq.com/assets/logos/cursor.png",
  });
  assert.match(card, /href="tools\/cursor\.html"/);
  assert.match(card, /src="https:\/\/agentscouthq\.com\/assets\/logos\/cursor\.png"/);
  const poisoned = cardFor({
    name: "<script>",
    slug: "bad\"><script>",
    category: "coding",
    pricing: "Free",
    description: "<i>",
    logo: "javascript:alert(1)",
  });
  assert.equal(poisoned.includes("<script>"), false);
  assert.match(poisoned, /href="#"/);
  assert.equal(poisoned.includes("javascript:"), false);
  load("../generate.js", context);
  assert.equal(context.asSafeArt("assets/gen-art.webp?v=2026-11-09"), "assets/gen-art.webp?v=2026-11-09");
  assert.equal(context.asSafeArt("assets/../secret"), "");
  assert.equal(context.asSafeArt("https://evil.example/x.png"), "");
  assert.equal(context.asSafeArt("assets/x.webp\");}</style>"), "");
});
