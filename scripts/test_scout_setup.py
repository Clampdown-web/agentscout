#!/usr/bin/env python3
"""Scout's page should say how the README actually starts the agent.

The npm package has no model. The quick start uses Outcrawl's cloud browser
unless you switch the browser setting. The maker's cloud benchmark number
stays off this listing.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ScoutSetupTests(unittest.TestCase):
    def setUp(self):
        self.rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))["scout-outcrawl"]
        self.page = (ROOT / "tools" / "scout-outcrawl.html").read_text(encoding="utf-8")

    def test_readme_steps_are_on_the_page_and_the_benchmark_number_is_not(self):
        blob = json.dumps(self.rich)
        for text in (
            "npm i @outcrawl/scout",
            "Node 22",
            "SCOUT_HANDS_MODEL",
            "browser: 'outcrawl'",
            "1,000 credits a month",
            "playwright-core",
            "replayUrl",
            "Apache-2.0",
            "agenthands",
        ):
            self.assertIn(text, blob)
            self.assertIn(text.replace("'", "&#x27;"), self.page if "'" in text else self.page)
        self.assertNotIn("92.5", blob)
        self.assertNotIn("92.5", self.page)
        self.assertIn(">Setup</h2>", self.page)
        self.assertIn('href="https://agentscouthq.com/tools/scout-outcrawl.html"', self.page)
        self.assertNotIn('content="noindex', self.page)
        self.assertIn("947", self.page)
        self.assertIn('"dateModified": "2026-10-19"', self.page)

    def test_the_other_three_priority_listings_are_untouched(self):
        rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))
        self.assertIn("Hobby €7/month", " ".join(rich["cloudcli"]["features"]))
        self.assertIn("$49", " ".join(rich["antinode-clear"]["features"]))
        self.assertIn("Plus $30/mo", " ".join(rich["luma-dream-machine"]["features"]))


if __name__ == "__main__":
    unittest.main()
