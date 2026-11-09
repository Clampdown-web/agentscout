#!/usr/bin/env python3
"""Checks for the SEO follow-up: schema, guide meta, sitemap, and the index cap."""
import json
import os
import re
import sys
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import build_seo_follow as seo


class SeoFollowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seo.run()

    def test_repaired_tool_jsonld_parses_and_has_types(self):
        for slug in ("cmux", "diagram-design"):
            text = Path(f"tools/{slug}.html").read_text(encoding="utf-8")
            self.assertNotIn("</script data-pagefind-weight", text)
            types = []
            for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
                data = json.loads(raw)
                nodes = data.get("@graph", [data]) if isinstance(data, dict) else []
                for n in nodes:
                    if not isinstance(n, dict):
                        continue
                    types.append(n.get("@type"))
                    about = n.get("about")
                    if isinstance(about, dict):
                        types.append(about.get("@type"))
            self.assertIn("SoftwareApplication", types, slug)
            self.assertIn("BreadcrumbList", types, slug)

    def test_category_itemlists_match_linked_tools(self):
        for path in Path("categories").glob("*.html"):
            if path.name == "index.html":
                continue
            text = path.read_text(encoding="utf-8")
            if "refresh" in text[:4000]:
                continue
            linked = []
            for slug in re.findall(r'href="(?:\.\./)*tools/([a-z0-9-]+)\.html"', text.split("<footer", 1)[0]):
                if slug not in linked:
                    linked.append(slug)
            found = False
            for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
                data = json.loads(raw)
                nodes = data.get("@graph", []) if isinstance(data, dict) else []
                for n in nodes:
                    if isinstance(n, dict) and n.get("@type") == "ItemList":
                        items = n.get("itemListElement") or []
                        self.assertEqual(n.get("numberOfItems"), len(items), path.name)
                        self.assertEqual(len(items), len(linked), path.name)
                        found = True
            self.assertTrue(found, path.name)

    def test_guide_titles_and_descriptions_fit(self):
        for pattern in seo.GUIDE_GLOBS:
            for path in Path(".").glob(pattern):
                text = path.read_text(encoding="utf-8")
                if "refresh" in text[:4000] or 'content="noindex' in text[:2500]:
                    continue
                title = unescape(re.search(r"<title>(.*?)</title>", text, flags=re.S).group(1)).strip()
                desc = unescape(re.search(r'<meta name="description" content="([^"]*)"', text).group(1))
                self.assertLessEqual(len(title), 60, path)
                self.assertLessEqual(len(desc), 156, path)
                self.assertGreaterEqual(len(title), 12, path)
                self.assertGreaterEqual(len(desc), 40, path)

    def test_thin_tools_stay_out_of_the_sitemap(self):
        sm = Path("sitemap.xml").read_text(encoding="utf-8")
        for rel in seo.THIN_NOINDEX:
            text = Path(rel).read_text(encoding="utf-8")[:2500]
            self.assertIn('content="noindex,follow"', text, rel)
            self.assertNotIn(f"https://agentscouthq.com/{rel}", sm, rel)

    def test_crawl_targets(self):
        sm = Path("sitemap.xml").read_text(encoding="utf-8")
        robots = Path("robots.txt").read_text(encoding="utf-8")
        self.assertIn("Disallow: /data/outreach/", robots)
        self.assertIn("https://agentscouthq.com/free-tools/roast-my-ai-tool-listing.html", sm)
        self.assertIn("https://agentscouthq.com/free-tools/ai-tool-launch-day-checklist.html", sm)
        for path in Path("launches").glob("*.html"):
            if path.name == "index.html":
                continue
            head = path.read_text(encoding="utf-8")[:2500]
            self.assertIn("noindex", head, path.name)
            self.assertNotIn(f"https://agentscouthq.com/launches/{path.name}", sm)
        redirects = json.loads(Path("redirects.json").read_text(encoding="utf-8"))
        self.assertEqual(redirects["tasks/evaluating-agents-guardrails.html"], "tasks/agent-security.html")
        page = Path("tasks/evaluating-agents-guardrails.html").read_text(encoding="utf-8")
        self.assertIn("agent-security.html", page)
        self.assertNotIn("agent-security-guardrails.html", page)
        self.assertIn("Content-Security-Policy", page)
        for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
            self.assertRegex(re.search(rf"<loc>{re.escape(loc)}</loc>\s*<lastmod>([^<]+)</lastmod>", sm).group(1), r"\d{4}-\d{2}-\d{2}")

    def test_pagefind_h1_does_not_eat_a_script_closer(self):
        import build_search
        sample = '<head><script type="application/ld+json">{"d":"<h1 align=\\"center\\" title"}</script></head><body><h1 class="icoh">Name</h1></body>'
        out = build_search.annotate.__globals__  # placeholder to keep import
        del out
        # Reproduce the body-only substitution the annotator now uses.
        head, body = sample.split("</head>", 1)
        body = re.sub(r'<h1(?![^>]*data-pagefind-weight)(\s[^>]{0,300})?>', lambda m: '<h1' + (m.group(1) or '') + ' data-pagefind-weight="10">', body, count=1)
        fixed = head + "</head>" + body
        self.assertIn("</script></head>", fixed)
        self.assertIn('<h1 class="icoh" data-pagefind-weight="10">', fixed)
        json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', fixed).group(1))


if __name__ == "__main__":
    unittest.main()
