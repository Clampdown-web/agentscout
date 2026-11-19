#!/usr/bin/env python3
"""The crawl how-to stays indexable, linked, and inside the generators."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "guides" / "how-to-crawl-websites-for-ai-agents.html"
HUB = ROOT / "guides" / "index.html"
QUERY = "how to crawl websites for ai agents"
CANON = "https://agentscouthq.com/guides/how-to-crawl-websites-for-ai-agents.html"
ALLOWED_TOOLS = {
    "firecrawl", "crawl4ai", "scrapegraphai", "scrapegraph-mcp", "scrapling",
    "scout-outcrawl", "spider", "browser-use", "stagehand", "playwright-mcp",
    "browserbase", "steel", "tavily", "exa", "n8n",
}
LINKED = [
    "tasks/web-scraping.html",
    "tasks/browsing-the-web-web-scraping.html",
    "s/free-ai-web-scraping-tools.html",
    "mcp/web-search-and-scraping-mcp-servers.html",
    "tools/firecrawl.html",
    "tools/crawl4ai.html",
]
ANSWER = "An AI web crawler fetches pages, renders JavaScript when needed, and returns clean Markdown or JSON a model can read."


class CrawlGuideTests(unittest.TestCase):
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
        # 64 chars: the brief's title leads with the top Search Console query
        # ("ai web crawler"); the per-guide cap in build_guides.GUIDES is 65.
        self.assertLessEqual(len(title), 65)
        self.assertLessEqual(len(desc), 156)
        self.assertIn(f'<link rel="canonical" href="{CANON}">', self.page)
        self.assertIn('name="robots" content="index, follow"', self.page)
        self.assertNotIn("noindex", self.page.lower())
        self.assertIn(CANON, self.sitemap)
        self.assertIn("https://agentscouthq.com/guides/", self.sitemap)
        self.assertIn(CANON, self.llms)

    def test_answer_box_first(self):
        self.assertIn(ANSWER, self.page)
        self.assertLess(self.page.index(ANSWER), self.page.index(">Steps<"))

    def test_jsonld_matches_the_visible_faq_and_steps(self):
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.page)
        graph = json.loads(blocks[-1])["@graph"]
        types = {node["@type"] for node in graph}
        self.assertEqual(types, {"HowTo", "FAQPage", "Article", "BreadcrumbList"})
        howto = next(node for node in graph if node["@type"] == "HowTo")
        self.assertEqual(len(howto["step"]), 8)
        for step in howto["step"]:
            self.assertIn(step["name"], self.page)
            self.assertIn(step["text"], self.page)
        faq = next(node for node in graph if node["@type"] == "FAQPage")
        self.assertEqual(len(faq["mainEntity"]), 7)
        for q in faq["mainEntity"]:
            self.assertIn(q["name"], self.page)
            self.assertIn(q["acceptedAnswer"]["text"], self.page)
        self.assertEqual(self.page.count('<th scope="col">'), 6)

    def test_tool_links_are_enriched_and_in_sitemap(self):
        hrefs = set(re.findall(r'href="\.\./tools/([a-z0-9-]+)\.html"', self.page))
        self.assertTrue(hrefs)
        self.assertTrue(hrefs <= ALLOWED_TOOLS, f"unenriched tool links: {hrefs - ALLOWED_TOOLS}")
        for slug in hrefs:
            self.assertIn(f"https://agentscouthq.com/tools/{slug}.html", self.sitemap, slug)

    def test_generators_and_contextual_links(self):
        self.assertIn("GUIDES", (ROOT / "build_guides.py").read_text(encoding="utf-8"))
        self.assertIn("build_guides.pages()", (ROOT / "build_extras.py").read_text(encoding="utf-8"))
        for rel in LINKED:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("guides/how-to-crawl-websites-for-ai-agents.html", text, rel)
        self.assertIn('href="how-to-crawl-websites-for-ai-agents.html"', self.hub)
        self.assertIn('content="index, follow"', self.hub)


if __name__ == "__main__":
    unittest.main()
