#!/usr/bin/env python3
"""The save/vote boot must not throw when app.js did not run.

Google's 2026-11-07 live test of tools/magentic-ui.html failed app.js with
"Other error" and the inline boot threw ReferenceError: AS is not defined.
The same boot is on category pages. Infra loaded app.js and had no console error.
"""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
import as_boot


NODE = r"""
const vm = require("vm");
const boot = process.argv[1];
function run(withAS) {
  const calls = [];
  const el = () => ({
    dataset: { actions: "x", save: "x", vote: "x" },
    parentNode: { querySelector() { return {}; } },
    classList: { toggle() {} },
    setAttribute() {},
    querySelector() { return { textContent: "" }; },
  });
  const list = { forEach(fn) { fn(el()); } };
  const document = { querySelectorAll() { calls.push("q"); return list; } };
  const context = { document };
  if (withAS) {
    context.AS = {
      saveBtn() { return ""; },
      voteBtn() { return ""; },
      saved() { return false; },
      voted() { return false; },
      bind() { calls.push("bind"); },
      savedCount() { calls.push("count"); return 0; },
    };
  }
  vm.createContext(context);
  vm.runInContext(boot, context);
  return calls;
}
const missing = run(false);
const present = run(true);
if (!present.includes("bind") || !present.includes("count")) {
  console.error("guard skipped a loaded AS");
  process.exit(2);
}
console.log("ok", missing.length, present.join(","));
"""


class AsBootGuardTests(unittest.TestCase):
    def test_template_and_tested_pages_skip_a_missing_as(self):
        pages = [
            ROOT / "data" / "detail.tpl",
            ROOT / "tools" / "magentic-ui.html",
            ROOT / "tools" / "scout-outcrawl.html",
            ROOT / "tools" / "cloudcli.html",
            ROOT / "tools" / "antinode-clear.html",
            ROOT / "tools" / "luma-dream-machine.html",
            ROOT / "categories" / "agent-infra.html",
            ROOT / "tools" / "cursor.html",
            ROOT / "tools" / "koog.html",
        ]
        for path in pages:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(as_boot.OLD, text, path.name)
            self.assertIn(as_boot.NEW, text, path.name)
            self.assertNotIn("window.AS", as_boot.NEW)
            script = as_boot.NEW[len("<script>"):-len("</script>")]
            out = subprocess.run(
                ["node", "-e", NODE, script],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(out.returncode, 0, out.stderr or out.stdout)
            self.assertIn("ok", out.stdout)

    def test_unguarded_boot_throws_without_as(self):
        raw = as_boot.OLD[len("<script>"):-len("</script>")]
        node = r"""
const vm = require("vm");
const boot = process.argv[1];
const document = { querySelectorAll() { return { forEach() {} }; } };
try {
  vm.runInContext(boot, vm.createContext({ document }));
  process.exit(3);
} catch (e) {
  if (e.name !== "ReferenceError") throw e;
  console.log("ReferenceError");
}
"""
        out = subprocess.run(
            ["node", "-e", node, raw],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("ReferenceError", out.stdout)

    def test_an_empty_window_as_does_not_count_as_loaded(self):
        """app.js binds lexical AS. window.AS is a later empty object."""
        script = as_boot.NEW[len("<script>"):-len("</script>")]
        node = r"""
const vm = require("vm");
const boot = process.argv[1];
const calls = [];
const el = () => ({
  dataset: { actions: "x", save: "x", vote: "x" },
  parentNode: { querySelector() { return {}; } },
  classList: { toggle() {} },
  setAttribute() {},
  querySelector() { return { textContent: "" }; },
});
const document = { querySelectorAll() { return { forEach(fn) { fn(el()); } }; } };
const windowAS = { saveBtn() { calls.push("window"); return ""; } };
vm.runInContext(boot, vm.createContext({ document, window: { AS: windowAS } }));
if (calls.length) process.exit(2);
const AS = {
  saveBtn() { return ""; }, voteBtn() { return ""; },
  saved() { return false; }, voted() { return false; },
  bind() { calls.push("bind"); }, savedCount() { calls.push("count"); return 0; },
};
vm.runInContext(boot, vm.createContext({ document, AS, window: { AS: {} } }));
if (!calls.includes("bind") || !calls.includes("count") || calls.includes("window")) process.exit(3);
console.log("lexical");
"""
        out = subprocess.run(
            ["node", "-e", node, script],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr or out.stdout)
        self.assertIn("lexical", out.stdout)

    def test_priority_listing_text_stays_with_the_guard(self):
        checks = {
            "tools/scout-outcrawl.html": "npm i @outcrawl/scout",
            "tools/cloudcli.html": "€7/month",
            "tools/antinode-clear.html": "formerly Supertone Clear",
            "tools/luma-dream-machine.html": "Plus $30/mo",
            "tools/magentic-ui.html": "MagenticLite is the next generation of Magentic-UI",
            "categories/agent-infra.html": 'id="choose"',
        }
        for rel, marker in checks.items():
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(marker, text, rel)
            self.assertIn(as_boot.NEW, text, rel)
            self.assertNotIn('content="noindex', text, rel)

    def test_guard_is_idempotent_and_the_next_build_applies_it(self):
        self.assertEqual(as_boot.guard(as_boot.OLD), as_boot.NEW)
        self.assertEqual(as_boot.guard(as_boot.NEW), as_boot.NEW)
        source = (ROOT / "build_tasks.py").read_text(encoding="utf-8")
        self.assertIn("s=as_boot.guard(s)", source)

    def test_updated_date_follows_verified_not_the_http_clock(self):
        tool = next(
            x for x in json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
            if x["slug"] == "magentic-ui"
        )
        expect = max(tool.get("verified") or "", tool.get("added") or "")
        self.assertEqual(tool["added"], "2026-10-16")
        self.assertEqual(expect, "2026-11-07")
        html = (ROOT / "tools" / "magentic-ui.html").read_text(encoding="utf-8")
        self.assertIn('datetime="2026-11-07"', html)
        self.assertIn('"dateModified": "2026-11-07"', html)
        self.assertIn("<dd>2026-10-16</dd>", html)
        self.assertIn('data-pagefind-sort="date:2026-10-16"', html)
        self.assertEqual(tool["github_stars"], 10108)


if __name__ == "__main__":
    unittest.main()
