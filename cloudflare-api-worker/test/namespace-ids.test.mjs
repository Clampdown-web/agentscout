import test from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

// Live agentscout-image namespaces are not in a wrangler file in this repo.
// docs/recovery-plan.md records them. They share a counter with any other
// worker that binds the same namespace_id, and the first limit wins.
const RESERVED_IMAGE = [
  { name: "TRACK_RL", namespace_id: "1001", limit: 20, period: 60, file: "docs/recovery-plan.md" },
  { name: "REVIEW_RL", namespace_id: "1002", limit: 6, period: 60, file: "docs/recovery-plan.md" },
  { name: "READY_RL", namespace_id: "1003", limit: 10, period: 60, file: "docs/recovery-plan.md" },
];

function stripJsonc(text) {
  let out = "";
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      const start = i;
      i += 1;
      while (i < text.length) {
        if (text[i] === "\\") { i += 2; continue; }
        if (text[i] === '"') { i += 1; break; }
        i += 1;
      }
      out += text.slice(start, i);
      i -= 1;
      continue;
    }
    if (ch === "/" && text[i + 1] === "/") {
      while (i < text.length && text[i] !== "\n") i += 1;
      i -= 1;
      continue;
    }
    if (ch === "/" && text[i + 1] === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      i += 1;
      continue;
    }
    out += ch;
  }
  return out;
}

function ratelimitEntries(text, file, worker) {
  if (file.endsWith(".toml")) {
    return text.split(/^\[\[ratelimits\]\]\s*$/m).slice(1).map((block) => {
      const body = block.split(/^\[\[/m)[0];
      return {
        worker,
        file,
        name: /name\s*=\s*"([^"]+)"/.exec(body)?.[1] || "",
        namespace_id: /namespace_id\s*=\s*"?(\d+)"?/.exec(body)?.[1] || "",
        limit: Number(/limit\s*=\s*(\d+)/.exec(body)?.[1]),
        period: Number(/period\s*=\s*(\d+)/.exec(body)?.[1]),
      };
    });
  }
  const json = JSON.parse(stripJsonc(text));
  const list = Array.isArray(json?.ratelimits) ? json.ratelimits : [];
  return list.map((entry) => ({
    worker,
    file,
    name: String(entry.name || ""),
    namespace_id: String(entry.namespace_id ?? ""),
    limit: Number(entry.simple?.limit),
    period: Number(entry.simple?.period),
  }));
}

export function ratelimitProblems(entries) {
  const problems = [];
  const byWorker = new Map();
  for (const entry of entries) {
    if (!/^[1-9]\d*$/.test(entry.namespace_id)) {
      problems.push(`${entry.file} ${entry.name || "(unnamed)"} namespace_id must be a positive integer`);
    }
    if (!Number.isInteger(entry.limit) || entry.limit < 1 || !Number.isInteger(entry.period) || entry.period < 1) {
      problems.push(`${entry.file} ${entry.name || "(unnamed)"} needs a positive limit and period`);
    }
    const list = byWorker.get(entry.worker) || [];
    list.push(entry);
    byWorker.set(entry.worker, list);
  }
  const owner = new Map();
  for (const [worker, list] of byWorker) {
    const seen = new Map();
    for (const entry of list) {
      const prev = seen.get(entry.namespace_id);
      if (!prev) {
        seen.set(entry.namespace_id, entry);
        continue;
      }
      if (prev.name !== entry.name || prev.limit !== entry.limit || prev.period !== entry.period) {
        problems.push(`${worker} namespace_id ${entry.namespace_id} is ${prev.name} ${prev.limit}/${prev.period}s (${prev.file}) and ${entry.name} ${entry.limit}/${entry.period}s (${entry.file})`);
      }
    }
    for (const entry of seen.values()) {
      const other = owner.get(entry.namespace_id);
      if (!other) {
        owner.set(entry.namespace_id, entry);
        continue;
      }
      if (other.worker !== worker) {
        problems.push(`namespace_id ${entry.namespace_id} is shared by ${other.worker} ${other.name} (${other.file}) and ${worker} ${entry.name} (${entry.file})`);
      }
    }
  }
  return problems;
}

async function loadEntries() {
  const names = await readdir(root, { recursive: true });
  const files = names.filter((rel) => {
    const text = String(rel);
    if (text.includes(`${path.sep}node_modules${path.sep}`) || text.includes(`${path.sep}.git${path.sep}`)) return false;
    return /(^|[\\/])wrangler[^\\/]*\.(toml|jsonc)$/.test(text);
  });
  const entries = [];
  for (const rel of files) {
    const file = String(rel);
    const worker = file.split(path.sep)[0];
    const text = await readFile(path.join(root, file), "utf8");
    entries.push(...ratelimitEntries(text, file, worker));
  }
  for (const reserved of RESERVED_IMAGE) {
    entries.push({ ...reserved, worker: "cloudflare-image-worker-patches" });
  }
  return entries;
}

test("a shared ratelimit namespace_id is a failure, and the same worker may repeat one binding", () => {
  const shared = ratelimitProblems([
    { worker: "agentscout-image", file: "image.toml", name: "TRACK_RL", namespace_id: "1001", limit: 20, period: 60 },
    { worker: "agentscout-api", file: "votes.toml", name: "ROAST_RL", namespace_id: "1001", limit: 8, period: 60 },
  ]);
  assert.equal(shared.length, 1);
  assert.match(shared[0], /1001/);
  assert.match(shared[0], /agentscout-image/);
  assert.match(shared[0], /agentscout-api/);

  const drifted = ratelimitProblems([
    { worker: "mcp", file: "wrangler.toml", name: "MCP_BURST", namespace_id: "481015", limit: 15, period: 10 },
    { worker: "mcp", file: "wrangler.jsonc", name: "MCP_BURST", namespace_id: "481015", limit: 60, period: 60 },
  ]);
  assert.equal(drifted.length, 1);

  const repeated = ratelimitProblems([
    { worker: "mcp", file: "wrangler.toml", name: "MCP_BURST", namespace_id: "481015", limit: 15, period: 10 },
    { worker: "mcp", file: "wrangler.jsonc", name: "MCP_BURST", namespace_id: "481015", limit: 15, period: 10 },
  ]);
  assert.deepEqual(repeated, []);
});

test("no two workers share a ratelimit namespace_id", async () => {
  const entries = await loadEntries();
  assert.ok(entries.length >= 7, `expected image, MCP, and votes bindings, got ${entries.length}`);
  assert.deepEqual(ratelimitProblems(entries), []);

  const votes = entries.filter((entry) => entry.worker === "cloudflare-api-worker");
  const roast = votes.find((entry) => entry.name === "ROAST_RL");
  const vote = votes.find((entry) => entry.name === "VOTE_RL");
  const src = await readFile(path.join(root, "cloudflare-api-worker/src/worker.js"), "utf8");
  assert.equal(roast.namespace_id, "481308");
  assert.equal(vote.namespace_id, "481330");
  assert.equal(roast.limit, Number(/const ROAST_PER_MIN = (\d+)/.exec(src)[1]));
  assert.equal(vote.limit, Number(/const VOTE_PER_MIN = (\d+)/.exec(src)[1]));
  assert.equal(roast.period, 60);
  assert.equal(vote.period, 60);
  assert.equal(roast.limit, 8);
  assert.equal(vote.limit, 30);
});
