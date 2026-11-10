import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("./submit-turnstile.js", import.meta.url), "utf8");
vm.runInThisContext(source);
const ts = globalThis.AgentScoutTurnstile;

function el(id, extra = {}) {
  return {
    id,
    hidden: true,
    textContent: "",
    dataset: {},
    attributes: {},
    listeners: {},
    classList: { contains(name) { return (extra.classes || []).includes(name); } },
    getAttribute(name) { return this.attributes[name]; },
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(type, fn) { this.listeners[type] = fn; },
    querySelector() { return extra.shown || null; },
    getBoundingClientRect() { return extra.rect || { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 }; },
    scrollIntoView() { this.scrolled = true; },
  };
}

function mountDom() {
  const nodes = {
    "sf-turnstile": el("sf-turnstile"),
    sfts: el("sfts"),
    "sfts-retry": el("sfts-retry"),
    "sfts-retry-wrap": el("sfts-retry-wrap"),
  };
  nodes["sf-turnstile"].attributes["data-sitekey"] = ts.SITEKEY;
  const head = { child: null, appendChild(node) { this.child = node; } };
  globalThis.document = {
    getElementById(id) { return nodes[id] || null; },
    createElement() { return { src: "", async: false, defer: false }; },
    head,
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  return { nodes, head };
}

test("retryable widget codes get a bounded automatic reset", () => {
  assert.equal(ts.planWidgetError("600010", 0).auto, true);
  assert.equal(ts.planWidgetError("600010", 0).fresh, false);
  assert.equal(ts.planWidgetError(600010, 1).auto, true);
  assert.equal(ts.planWidgetError("600010", 2).auto, false);
  assert.equal(ts.planWidgetError("600010", 2).fresh, true);
  assert.match(ts.planWidgetError("600010", 2).text, /Trying again automatically/);
  assert.match(ts.planWidgetError("600010", 2).text, /Nothing was sent/);
  assert.equal(ts.planWidgetError("600010", 2, 1).fresh, false);
  assert.match(ts.planWidgetError("600010", 2, 1).text, /Try the check again/);
  assert.equal(ts.planWidgetError("300010", 2, 0).fresh, false);
  assert.match(ts.planWidgetError("300010", 2, 0).text, /Try the check again/);
  assert.equal(ts.planWidgetError("110200", 0, 0).fresh, false);
  assert.equal(ts.planWidgetError("600010", 0).suppressBuiltinRetry, true);
  assert.equal(ts.retryable("110200"), false);
  assert.equal(ts.retryable("400020"), false);
  assert.equal(ts.retryable("200100"), false);
  assert.equal(ts.retryable("110600"), true);
  assert.equal(ts.retryable("300010"), true);
  assert.equal(ts.retryable(""), false);
});

test("a token is not replayed after any HTTP response", () => {
  assert.equal(ts.nextEndpoint(500, 0, 2), -1);
  assert.equal(ts.nextEndpoint(403, 0, 2), -1);
  assert.equal(ts.nextEndpoint(200, 0, 2), -1);
  assert.equal(ts.nextEndpoint(null, 0, 2), 1);
  assert.equal(ts.nextEndpoint(null, 1, 2), -1);
  assert.equal(ts.tokenUsable("", false), false);
  assert.equal(ts.tokenUsable("abc", true), false);
  assert.equal(ts.tokenUsable("x".repeat(2049), false), false);
  assert.equal(ts.tokenUsable("fresh-token", false), true);
  assert.match(ts.submitFailureText("Bot check failed."), /Complete the check again/);
  assert.match(ts.submitFailureText("The check expired or was already used. Complete it again, then submit."), /Complete it again/);
  assert.equal(ts.widgetSize(0), "compact");
  assert.equal(ts.widgetSize(288), "compact");
  assert.equal(ts.widgetSize(300), "flexible");
  assert.equal(ts.widgetSize(358), "flexible");
  assert.equal(ts.ACTION, "submit");
  assert.equal(ts.SITEKEY, "0x4AAAAAAFfaxf14aQF-sky1");
  assert.match(ts.SCRIPT, /render=explicit&onload=asTsLoad/);
});

test("an explicit widget renders once, retries twice, then offers a button", async () => {
  const originalFetch = globalThis.fetch;
  const urls = [];
  globalThis.fetch = async (url) => {
    urls.push(String(url));
    if (urls.length === 1) return new Response(JSON.stringify({ error: "Bot check failed." }), { status: 500, headers: { "content-type": "application/json" } });
    return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } });
  };
  try {
    await assert.rejects(() => ts.postJson(["https://primary.example/submit", "https://fallback.example/submit"], "{\"turnstileToken\":\"spent\"}"), /Bot check failed/);
    assert.deepEqual(urls, ["https://primary.example/submit"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
  const failover = [];
  globalThis.fetch = async (url) => {
    failover.push(String(url));
    if (failover.length === 1) throw new Error("connection reset");
    return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } });
  };
  try {
    const body = await ts.postJson(["https://primary.example/submit", "https://fallback.example/submit"], "{}");
    assert.equal(body.ok, true);
    assert.deepEqual(failover, ["https://primary.example/submit", "https://fallback.example/submit"]);
  } finally {
    globalThis.fetch = originalFetch;
  }

  const { nodes, head } = mountDom();
  const resets = [];
  const removed = [];
  const renders = [];
  let seq = 0;
  globalThis.turnstile = {
    render(el, options) {
      assert.equal(el, nodes["sf-turnstile"]);
      assert.equal(options.sitekey, ts.SITEKEY);
      assert.equal(options.action, "submit");
      assert.equal(options.retry, "never");
      assert.equal(options["refresh-expired"], "auto");
      assert.equal(options["refresh-timeout"], "auto");
      assert.equal(typeof options["error-callback"], "function");
      this.options = options;
      const id = "widget-" + (++seq);
      renders.push(id);
      return id;
    },
    reset(id) { resets.push(id); },
    remove(id) { removed.push(id); },
    getResponse(id) { return renders.includes(id) ? "token-1" : ""; },
    isExpired() { return false; },
  };
  globalThis.scrollBy = () => {};
  ts.start();
  assert.equal(head.child, null);
  globalThis.asTsLoad();
  globalThis.asTsLoad();
  assert.deepEqual(renders, ["widget-1"]);
  assert.equal(ts.readToken(), "token-1");
  assert.equal(globalThis.asTsErr(600010), true);
  assert.match(nodes.sfts.textContent, /600010/);
  assert.match(nodes.sfts.textContent, /Trying again automatically/);
  assert.equal(nodes["sfts-retry-wrap"].hidden, true);
  await new Promise((resolve) => setTimeout(resolve, ts.AUTO_MS + 50));
  assert.deepEqual(resets, ["widget-1"]);
  assert.equal(globalThis.asTsErr("600010"), true);
  await new Promise((resolve) => setTimeout(resolve, ts.AUTO_MS + 50));
  assert.equal(resets.length, 2);
  assert.deepEqual(removed, []);
  assert.equal(globalThis.asTsErr(600010), true);
  assert.equal(nodes["sfts-retry-wrap"].hidden, true);
  assert.match(nodes.sfts.textContent, /Trying again automatically/);
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.deepEqual(removed, ["widget-1"]);
  assert.deepEqual(renders, ["widget-1", "widget-2"]);
  assert.equal(resets.length, 2);
  assert.equal(globalThis.asTsErr(600010), true);
  assert.equal(nodes["sfts-retry-wrap"].hidden, false);
  assert.match(nodes.sfts.textContent, /Try the check again/);
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.deepEqual(removed, ["widget-1"]);
  assert.equal(resets.length, 2);
  nodes["sfts-retry"].listeners.click();
  assert.equal(resets.length, 3);
  assert.equal(resets[2], "widget-2");
  globalThis.asTsOk("token-2");
  assert.equal(nodes.sfts.textContent, "");
  assert.equal(nodes["sfts-retry-wrap"].hidden, true);
  globalThis.turnstile.isExpired = () => true;
  assert.equal(ts.readToken(), "");
  globalThis.turnstile.isExpired = () => false;
  globalThis.turnstile.getResponse = () => "";
  globalThis.document.querySelector = () => ({ value: "stale-spent-token" });
  assert.equal(ts.readToken(), "");
  ts.invalidate();
  assert.equal(resets.length, 4);
  assert.match(nodes.sfts.textContent, /Complete the check again/);
  assert.equal(ts.readToken() === "stale-spent-token", false);
});

test("asTsLoad works whether api.js finishes before or after this file", () => {
  function boot(extra) {
    const renders = [];
    const turnstileEl = {
      id: "sf-turnstile",
      attributes: { "data-sitekey": "0x4AAAAAAFfaxf14aQF-sky1" },
      getAttribute(name) { return this.attributes[name]; },
      getBoundingClientRect() { return { width: 360, height: 65, top: 400, left: 16, right: 316, bottom: 465 }; },
    };
    const sandbox = {
      asTsLoaded: extra.loaded ? 1 : 0,
      renders,
      document: {
        getElementById(id) { return id === "sf-turnstile" ? turnstileEl : null; },
        head: { child: null, appendChild(node) { this.child = node; } },
        querySelector() { return null; },
        querySelectorAll() { return []; },
        createElement() { return { src: "", async: false, defer: false }; },
        documentElement: { getAttribute() { return "light"; } },
      },
      setTimeout,
      clearTimeout,
    };
    if (extra.turnstileReady) {
      sandbox.turnstile = {
        render() { renders.push("now"); return "now"; },
        reset() {},
        remove() {},
        getResponse() { return ""; },
        isExpired() { return false; },
      };
    }
    vm.createContext(sandbox);
    vm.runInContext(source, sandbox);
    return sandbox;
  }

  const early = boot({ loaded: true, turnstileReady: true });
  early.AgentScoutTurnstile.start();
  assert.deepEqual(early.renders, ["now"]);
  assert.equal(early.document.head.child, null);

  const late = boot({ loaded: false, turnstileReady: false });
  late.AgentScoutTurnstile.start();
  assert.deepEqual(late.renders, []);
  late.turnstile = {
    render() { late.renders.push("late"); return "late"; },
    reset() {},
    remove() {},
    getResponse() { return "late-token"; },
    isExpired() { return false; },
  };
  late.asTsLoad();
  assert.deepEqual(late.renders, ["late"]);
  assert.equal(late.AgentScoutTurnstile.readToken(), "late-token");
  assert.equal(late.document.head.child, null);

  const queued = boot({ loaded: false, turnstileReady: false });
  queued.turnstile = {
    render() { queued.renders.push("queued"); return "queued"; },
    reset() {},
    remove() {},
    getResponse() { return ""; },
    isExpired() { return false; },
  };
  queued.asTsLoad();
  assert.deepEqual(queued.renders, []);
  queued.AgentScoutTurnstile.start();
  assert.deepEqual(queued.renders, ["queued"]);
  assert.equal(queued.document.head.child, null);
});
