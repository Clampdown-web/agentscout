import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const text = readFileSync(new URL("../.github/workflows/security.yml", import.meta.url), "utf8");

test("the security workflow is read-only, pinned, and does not deploy", () => {
  assert.match(text, /^permissions:\n {2}contents: read/m);
  const code = text.replace(/#[^\n]*/g, "");
  assert.equal(/pull_request_target\s*:/.test(code), false);
  assert.equal(code.includes("secrets."), false);
  assert.equal(/wrangler deploy|npx wrangler/i.test(text), false);
  const uses = [...text.matchAll(/uses: ([^\s#]+)/g)].map((match) => match[1]);
  assert.ok(uses.length >= 2);
  for (const action of uses) {
    assert.match(action, /@[0-9a-f]{40}$/);
  }
  assert.match(text, /persist-credentials: false/);
  const pythonJob = text.split("python-requirements:")[1] || "";
  assert.equal(pythonJob.includes("pip-audit"), true);
  assert.equal(pythonJob.includes("persist-credentials"), false);
});
