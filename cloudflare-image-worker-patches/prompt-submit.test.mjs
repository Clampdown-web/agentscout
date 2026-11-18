import test, { describe } from "node:test";
import assert from "node:assert/strict";
import {
  PROMPT_CATEGORIES,
  PROMPT_KEY_PREFIX,
  PROMPT_SUBJECT,
  handlePromptSubmit,
  isPromptSubmission,
  validatePromptSubmission,
} from "./prompt-submit.js";

/** Minimal Workers KV stand-in: put/get backed by a Map. */
function fakeKv() {
  const store = new Map();
  return {
    store,
    async put(key, value, options) {
      store.set(key, { value, options });
    },
    async get(key) {
      return store.has(key) ? store.get(key).value : null;
    },
  };
}

/** The exact shape the prompt form (submit.html?type=prompt, PR #160) posts. */
function promptBody(overrides = {}) {
  return {
    name: "Debug a failing test",
    website: "",
    github: "",
    category: "coding-agents",
    pricing: "Free",
    desc: "A prompt that walks a coding agent through a failing test.",
    prompt: "You are a senior engineer. Read the failing test output, find the root cause, and propose the smallest fix.",
    works_with: "Claude, Cursor",
    email: "maker@example.com",
    x: "maker",
    newsletter_optin: "no",
    company: "",
    type: "prompt",
    tool: "",
    how_found: "X (Twitter)",
    found: "X (Twitter)",
    found_other: "",
    turnstileToken: "test-token",
    ...overrides,
  };
}

function toolBody(overrides = {}) {
  return {
    name: "Some Tool",
    website: "",
    github: "",
    category: "MCP servers",
    pricing: "Free",
    desc: "A tool.",
    email: "maker@example.com",
    x: "",
    newsletter_optin: "no",
    company: "",
    type: "new",
    tool: "",
    how_found: "X (Twitter)",
    found: "X (Twitter)",
    found_other: "",
    turnstileToken: "test-token",
    ...overrides,
  };
}

describe("prompt submissions", { concurrency: false }, () => {
  test("prompt accepted without website, stored under prompt: prefix, never as a tool listing", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(promptBody(), kv, 1795019000000);
    assert.equal(result.handled, true);
    assert.equal(result.status, 200);
    assert.equal(result.body.ok, true);
    assert.equal(result.body.type, "prompt");
    assert.equal(kv.store.size, 1);
    const [key, stored] = [...kv.store.entries()][0];
    assert.ok(key.startsWith(PROMPT_KEY_PREFIX), key);
    assert.ok(!key.startsWith("sub:"), key);
    const record = JSON.parse(stored.value);
    assert.equal(record.type, "prompt");
    assert.equal(record.subject, PROMPT_SUBJECT);
    assert.equal(record.title, "Debug a failing test");
    assert.equal(record.category, "coding-agents");
    assert.match(record.prompt, /senior engineer/);
    assert.equal(record.works_with, "Claude, Cursor");
    assert.equal(record.website, "");
    assert.equal(record.ts, 1795019000);
    assert.ok(stored.options.expirationTtl > 0);
  });

  test("each prompt category is accepted", async () => {
    for (const category of PROMPT_CATEGORIES) {
      const kv = fakeKv();
      const result = await handlePromptSubmit(promptBody({ category }), kv);
      assert.equal(result.status, 200, category);
    }
  });

  test("bad prompt category rejected with 400 and nothing stored", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(promptBody({ category: "MCP servers" }), kv);
    assert.equal(result.handled, true);
    assert.equal(result.status, 400);
    assert.match(result.body.error, /category/i);
    assert.equal(kv.store.size, 0);
  });

  test("empty prompt rejected with 400 and nothing stored", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(promptBody({ prompt: "   " }), kv);
    assert.equal(result.status, 400);
    assert.match(result.body.error, /prompt/i);
    assert.equal(kv.store.size, 0);
  });

  test("missing title rejected with 400", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(promptBody({ name: "" }), kv);
    assert.equal(result.status, 400);
    assert.match(result.body.error, /title/i);
    assert.equal(kv.store.size, 0);
  });

  test("prompt longer than the form limit rejected with 400", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(promptBody({ prompt: "x".repeat(2001) }), kv);
    assert.equal(result.status, 400);
    assert.equal(kv.store.size, 0);
  });

  test("a website, when given, must be http/https", async () => {
    const kv = fakeKv();
    const bad = await handlePromptSubmit(promptBody({ website: "ftp://example.com/x" }), kv);
    assert.equal(bad.status, 400);
    assert.equal(kv.store.size, 0);
    const good = await handlePromptSubmit(promptBody({ website: "https://example.com/" }), kv);
    assert.equal(good.status, 200);
    const record = JSON.parse([...kv.store.values()][0].value);
    assert.equal(record.website, "https://example.com/");
  });

  test("tool submission without website is NOT handled here, so the tool path still rejects it", async () => {
    const kv = fakeKv();
    // The prompt branch must not accept or rewrite a tool submission; the
    // existing tool validation in handleSubmit still sees it and rejects
    // the empty website, exactly as before.
    const result = await handlePromptSubmit(toolBody(), kv);
    assert.equal(result.handled, false);
    assert.equal(kv.store.size, 0);
    assert.equal(isPromptSubmission(toolBody()), false);
  });

  test("update path unchanged: update submissions fall through", async () => {
    const kv = fakeKv();
    const result = await handlePromptSubmit(toolBody({ type: "update", tool: "some-tool", website: "https://example.com/" }), kv);
    assert.equal(result.handled, false);
    assert.equal(kv.store.size, 0);
  });

  test("a valid prompt never reaches the inner handler; a tool submission does, unchanged", async () => {
    const kv = fakeKv();
    const seen = [];
    const inner = {
      async fetch(request) {
        seen.push(await request.clone().json());
        return Response.json({ ok: true });
      },
    };
    // Simulate what handleSubmit does with the module: prompt first, else inner.
    async function submit(body) {
      const prompt = await handlePromptSubmit(body, kv);
      if (prompt.handled) return new Response(JSON.stringify(prompt.body), { status: prompt.status });
      return inner.fetch(new Request("https://api.agentscouthq.com/submit", {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "content-type": "application/json" },
      }));
    }
    const promptResponse = await submit(promptBody());
    assert.equal(promptResponse.status, 200);
    assert.equal(seen.length, 0);
    const toolResponse = await submit(toolBody({ website: "https://example.com/" }));
    assert.equal(toolResponse.status, 200);
    assert.equal(seen.length, 1);
    assert.equal(seen[0].type, "new");
    assert.equal(seen[0].website, "https://example.com/");
  });

  test("missing KV binding fails closed with 503, not as a tool listing", async () => {
    const result = await handlePromptSubmit(promptBody(), null);
    assert.equal(result.handled, true);
    assert.equal(result.status, 503);
  });

  test("validatePromptSubmission rejects a non-object body", () => {
    assert.equal(validatePromptSubmission(null).ok, false);
    assert.equal(validatePromptSubmission("prompt").ok, false);
  });
});
