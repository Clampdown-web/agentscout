import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

test("reviews.js puts the star count through a number before innerHTML", async () => {
  const elements = new Map();
  function element(html = "") {
    const node = {
      innerHTML: html,
      hidden: false,
      textContent: "",
      className: "",
      style: {},
      value: "",
      parentNode: null,
      children: [],
      setAttribute() {},
      getAttribute(name) { return name === "data-tool" ? "widget" : name === "data-name" ? "Widget" : ""; },
      querySelector(sel) { return elements.get(sel) || null; },
      insertAdjacentElement() {},
      addEventListener() {},
    };
    node.parentNode = node;
    return node;
  }
  const list = element();
  const sum = element();
  elements.set(".rv-sum", sum);
  elements.set(".rv-list", list);
  elements.set(".rv-form", null);
  const sec = element();
  sec.querySelector = (sel) => elements.get(sel) || null;
  const document = {
    getElementById(id) { return id === "reviews" ? sec : null; },
    querySelectorAll() { return []; },
    querySelector() { return null; },
    createElement() { return element(); },
    head: { appendChild() {} },
  };
  let html = "";
  const context = vm.createContext({
    document,
    location: { hash: "" },
    history: { replaceState() {} },
    fetch() {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          count: 1,
          avg: 5,
          reviews: [
            { stars: "<img src=x onerror=alert(1)>", name: "A", text: "hello", ts: 0 },
            { stars: 4, name: "<b>Eve</b>", text: "ok", ts: "not-a-date" },
          ],
        }),
      });
    },
    localStorage: { getItem() { return null; }, setItem() {} },
    crypto: { getRandomValues(buf) { buf.fill(1); return buf; } },
    setTimeout,
    console,
  });
  context.window = context;
  vm.runInContext(readFileSync(new URL("../reviews.js", import.meta.url), "utf8"), context);
  await new Promise((resolve) => setTimeout(resolve, 20));
  html = list.innerHTML;
  assert.equal(html.includes("<img"), false);
  assert.equal(html.includes("onerror"), false);
  assert.match(html, /0 out of 5 stars/);
  assert.match(html, /--r:0/);
  assert.match(html, /&lt;b&gt;Eve&lt;\/b&gt;/);
  assert.match(html, /datetime=""/);
});
