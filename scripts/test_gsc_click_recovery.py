#!/usr/bin/env python3
"""Indexability guard for the Oct 20-24 Web click pages.

Four tool URLs that earned a click were later marked noindex by the thin-page
rule (under 80 unique words and no enrichment). Enrichment from the maker's
own pages is the rule's existing way back into the sitemap. This test does
not raise the 5-new-URL cap and does not treat an unenriched short page as
indexable.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENRICHED = ("cloudcli", "antinode-clear", "luma-dream-machine", "scout-outcrawl")
FIELDS = ("long", "who", "features")


def _words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text))


class ClickRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = {x["slug"]: x for x in json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))}
        cls.rich = json.loads((ROOT / "tool_rich.json").read_text(encoding="utf-8"))
        cls.sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        cls.rule = (ROOT / "build_site.py").read_text(encoding="utf-8")
        cls.links = (ROOT / "build_intlinks.py").read_text(encoding="utf-8")

    def test_daily_cap_and_thin_threshold_unchanged(self):
        self.assertIn("NEW_TOOL_CAP=5", self.rule)
        self.assertIn("THIN_WORDS=80", self.rule)
        self.assertIn("if enr or (not thin and (grandfather or slug in slots)):", self.rule)

    def test_enriched_click_pages_are_eligible_and_in_the_sitemap(self):
        for slug in ENRICHED:
            record = self.rich[slug]
            self.assertEqual(record.get("kind"), "lite", slug)
            for field in FIELDS:
                self.assertTrue(record.get(field), slug + " " + field)
            prose = " ".join(record["long"]) + " " + record["who"] + " " + " ".join(record["features"])
            self.assertGreaterEqual(_words(prose), 80, slug)
            page = (ROOT / "tools" / f"{slug}.html").read_text(encoding="utf-8")
            self.assertNotIn('name="robots" content="noindex', page[:2500], slug)
            self.assertIn(f">What is {self.tools[slug]['name']}?</h2>", page, slug)
            self.assertIn(f"https://agentscouthq.com/tools/{slug}.html", self.sitemap)

    def test_enrichment_does_not_copy_an_unverified_benchmark(self):
        scout = json.dumps(self.rich["scout-outcrawl"])
        self.assertNotIn("92.5", scout)
        self.assertNotIn("81.4", scout)
        page = (ROOT / "tools" / "scout-outcrawl.html").read_text(encoding="utf-8")
        self.assertNotIn("92.5", page)

    def test_a_short_unenriched_page_stays_noindex(self):
        found = None
        for tool in self.tools.values():
            if tool["slug"] in self.rich:
                continue
            if _words(tool.get("description") or "") >= 80:
                continue
            path = ROOT / "tools" / f"{tool['slug']}.html"
            if not path.exists():
                continue
            head = path.read_text(encoding="utf-8")[:2500]
            if 'name="robots" content="noindex' not in head:
                continue
            loc = f"https://agentscouthq.com/tools/{tool['slug']}.html"
            self.assertNotIn(loc, self.sitemap)
            found = tool["slug"]
            break
        self.assertIsNotNone(found)

    def test_agent_infra_is_linked_and_the_old_best_url_is_not(self):
        self.assertIn('("categories/agent-infra.html"', self.links)
        self.assertNotIn("best/mcp-servers.html", self.links)
        n = sum(1 for tool in self.tools.values() if tool["category"] == "agent infra")
        # Nov 9 2026: homepage Popular lists pills removed; hub pages still carry the chip block.
        hub = (ROOT / "categories" / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'href="../categories/agent-infra.html">All {n:,} agent infra tools</a>', hub)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<!--il:pop-->", home)
        self.assertIn("<!--il:footpop-->", home)
        self.assertIn(
            'name="robots" content="noindex,follow"',
            (ROOT / "best" / "mcp-servers.html").read_text(encoding="utf-8")[:2000],
        )


if __name__ == "__main__":
    unittest.main()
