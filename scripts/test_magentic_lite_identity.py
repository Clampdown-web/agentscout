#!/usr/bin/env python3
"""MagenticLite identity: current README product, not the 0.1 name, stays indexable."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = (
    "https://www.microsoft.com/en-us/research/blog/"
    "magenticlite-magenticbrain-fara1-5-an-agentic-experience-optimized-for-small-models/"
)
REPO = "https://github.com/microsoft/magentic-ui"
PAGE = ROOT / "tools" / "magentic-ui.html"


class MagenticLiteIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = next(
            x for x in json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
            if x["slug"] == "magentic-ui"
        )
        cls.rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))["magentic-ui"]
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.rule = (ROOT / "build_site.py").read_text(encoding="utf-8")

    def test_catalog_names_the_current_release_and_keeps_verified_links(self):
        self.assertEqual(self.tool["name"], "MagenticLite")
        self.assertTrue(self.tool["description"].startswith(
            "MagenticLite is the next generation of Magentic-UI"
        ))
        self.assertEqual(self.tool["url"], BLOG)
        self.assertEqual(self.tool["website"], BLOG)
        self.assertEqual(self.tool["github"], REPO)
        self.assertEqual(self.tool["pricing"], "Open source")
        self.assertEqual(self.tool["github_stars"], 10108)
        self.assertEqual(self.tool["stars_checked"], "2026-10-30")

    def test_first_sentence_matches_the_readme(self):
        self.assertTrue(self.rich["long"][0].startswith(
            "MagenticLite is the next generation of Magentic-UI from Microsoft AI Frontiers."
        ))
        self.assertNotIn("its next generation, MagenticLite", self.rich["long"][0])
        body = re.search(r">What is MagenticLite\?</h2><p[^>]*>(.*?)</p>", self.html)
        self.assertIsNotNone(body)
        self.assertTrue(body.group(1).startswith(
            "MagenticLite is the next generation of Magentic-UI from Microsoft AI Frontiers."
        ))

    def test_page_stays_indexable_and_self_canonical(self):
        head = self.html[:2500]
        self.assertNotIn('name="robots" content="noindex', head)
        self.assertIn(
            'rel="canonical" href="https://agentscouthq.com/tools/magentic-ui.html"',
            self.html,
        )
        self.assertIn(BLOG, self.html)
        self.assertIn('href="https://github.com/microsoft/magentic-ui"', self.html)
        self.assertIn("<title>MagenticLite: next generation of Magentic-UI</title>", self.html)
        self.assertIn("<span>MagenticLite</span>", self.html)
        self.assertIn("10,108 (as of 2026-10-30)", self.html)
        self.assertNotIn("42.52", self.html)
        self.assertIn("NEW_TOOL_CAP=5", self.rule)
        self.assertIn("THIN_WORDS=80", self.rule)


if __name__ == "__main__":
    unittest.main()
