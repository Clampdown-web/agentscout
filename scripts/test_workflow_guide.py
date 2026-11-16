#!/usr/bin/env python3
"""The workflow how-to stays indexable, linked, and inside the generators."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "guides" / "how-to-automate-workflows-with-ai-agents.html"
HUB = ROOT / "guides" / "index.html"
QUERY = "how to automate workflows with ai agents"
CANON = "https://agentscouthq.com/guides/how-to-automate-workflows-with-ai-agents.html"
LINKED = [
    "s/free-ai-workflow-automation-tools.html",
    "s/open-source-workflow-automation-tools.html",
    "compare/n8n-vs-make.html",
    "compare/n8n-vs-zapier-agents.html",
    "best/no-code-ai-agent-builders.html",
    "tools/n8n.html",
]


class WorkflowGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = GUIDE.read_text(encoding="utf-8")
        cls.hub = HUB.read_text(encoding="utf-8")
        cls.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        cls.llms = (ROOT / "llms.txt").read_text(encoding="utf-8")

    def test_query_metadata_and_indexability(self):
        title = re.search(r"<title>(.*?)</title>", self.page, re.S).group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', self.page).group(1)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", self.page, re.S).group(1)
        self.assertIn(QUERY, title.lower())
        self.assertIn(QUERY, desc.lower())
        self.assertIn(QUERY, h1.lower())
        self.assertLessEqual(len(title), 60)
        self.assertLessEqual(len(desc), 156)
        self.assertIn(f'<link rel="canonical" href="{CANON}">', self.page)
        self.assertIn('name="robots" content="index, follow"', self.page)
        self.assertNotIn("noindex", self.page.lower())
        self.assertNotIn("tuesday", self.page.lower())
        self.assertIn("every Wednesday", self.page)
        self.assertIn(CANON, self.sitemap)
        self.assertIn("https://agentscouthq.com/guides/", self.sitemap)
        self.assertIn(CANON, self.llms)

    def test_jsonld_matches_the_visible_faq_and_steps(self):
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.page)
        graph = json.loads(blocks[-1])["@graph"]
        types = {node["@type"] for node in graph}
        self.assertEqual(types, {"HowTo", "FAQPage", "BreadcrumbList"})
        howto = next(node for node in graph if node["@type"] == "HowTo")
        self.assertEqual(len(howto["step"]), 8)
        for step in howto["step"]:
            self.assertIn(step["name"], self.page)
            self.assertIn(step["text"], self.page)
        faq = next(node for node in graph if node["@type"] == "FAQPage")
        self.assertEqual(len(faq["mainEntity"]), 6)
        for q in faq["mainEntity"]:
            self.assertIn(q["name"], self.page)
            self.assertIn(q["acceptedAnswer"]["text"], self.page)
        self.assertEqual(self.page.count('<th scope="col">'), 6)

    def test_generators_and_contextual_links(self):
        for rel in ("build_extras.py", "build_best.py", "build_landing.py", "build_rich.py", "build_seo.py", "build_og.py"):
            self.assertIn("guides", (ROOT / rel).read_text(encoding="utf-8"))
        self.assertIn("build_guides.pages()", (ROOT / "build_extras.py").read_text(encoding="utf-8"))
        for rel in LINKED:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("guides/how-to-automate-workflows-with-ai-agents.html", text, rel)
        self.assertIn('href="how-to-automate-workflows-with-ai-agents.html"', self.hub)
        self.assertIn('content="index, follow"', self.hub)


if __name__ == "__main__":
    unittest.main()
