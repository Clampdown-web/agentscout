#!/usr/bin/env python3
"""The agent-infra page names a starting tool for each common layer.

Descriptions are copied from tools.json. A slug that leaves agent infra drops out.
MagenticLite links to that list because its README says you bring a model endpoint.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
import quality_picks


class ChoiceGuideTests(unittest.TestCase):
    def setUp(self):
        self.tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
        self.by = {x["slug"]: x for x in self.tools}
        guides = json.loads((ROOT / "data" / "quality_guides.json").read_text(encoding="utf-8"))
        self.guide = next(g for g in guides if g["path"] == "categories/agent-infra.html")

    def test_rows_quote_the_listing_and_skip_a_tool_that_left_the_category(self):
        html = quality_picks.choice_html(self.guide["picks"], self.by, bridge=True)
        for row in self.guide["picks"]:
            for slug in row["slugs"]:
                tool = self.by[slug]
                self.assertEqual(tool["category"], "agent infra")
                self.assertIn(f'href="../tools/{slug}.html"', html)
                self.assertIn(tool["description"].rstrip("."), html)
        self.assertIn('href="../tools/magentic-ui.html"', html)
        self.assertIn('id="choose"', html)
        moved = dict(self.by)
        moved["litellm"] = dict(moved["litellm"], category="frameworks")
        without = quality_picks.choice_html(self.guide["picks"], moved, bridge=True)
        self.assertNotIn("litellm.html", without)
        self.assertIn("portkey-ai-gateway.html", without)

    def test_pages_include_the_guide_and_the_model_link(self):
        cat = (ROOT / "categories" / "agent-infra.html").read_text(encoding="utf-8")
        block = quality_picks.choice_html(self.guide["picks"], self.by, bridge=True)
        self.assertIn(block, cat)
        self.assertIn("Use Start with the job when you already know the layer", cat)
        self.assertIn('href="https://agentscouthq.com/categories/agent-infra.html"', cat)
        self.assertNotIn('content="noindex', cat)
        page = (ROOT / "tools" / "magentic-ui.html").read_text(encoding="utf-8")
        self.assertIn(quality_picks.model_note(), page)
        self.assertIn('href="../categories/agent-infra.html#choose"', page)
        self.assertIn('href="https://agentscouthq.com/tools/magentic-ui.html"', page)
        self.assertNotIn('content="noindex', page)
        extras = json.loads((ROOT / "data" / "quality_tool_extras.json").read_text(encoding="utf-8"))
        self.assertTrue(extras["magentic-ui"]["needs_model"])
        self.assertIn("quality_picks.choice_html", (ROOT / "build_quality.py").read_text(encoding="utf-8"))
        self.assertIn("quality_picks.model_note", (ROOT / "build_rich.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
