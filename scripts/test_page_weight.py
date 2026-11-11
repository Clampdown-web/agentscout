#!/usr/bin/env python3
"""Homepage and /new.html stay small after the catalog grew.

The homepage must not reference both catalog files (tools.json and
api/tools.json). /new.html lists full listings only, capped, and the
new-tool counts exclude catalog_only rows. Removed tools that 301 to a
category must not be linked from generated launch or alternatives pages.
"""
from __future__ import annotations

import os
import re
import sys
import unittest
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import atexit

import build_extras  # noqa: E402
import build_recent  # noqa: E402
import build_tasks  # noqa: E402

atexit.unregister(build_extras._apply_featured)

# 80 full listings plus the makers block. The old page was ~2.9 MB / 5,000 cards.
NEW_HTML_MAX_BYTES = 800_000
NEW_DATED_CARDS_MAX = 100
REMOVED = ("hindsight", "menlo-insurance-mcp", "mnemosyne", "agentsmesh")


def _bare_tools_json(html):
    """A tools.json reference that is not the api/tools.json feed."""
    return bool(re.search(r'(?<!api/)(?<!api\\/)tools\.json', html))


class HomepageCatalogTest(unittest.TestCase):
    def test_homepage_does_not_fetch_both_catalogs(self):
        html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        app = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()
        # The homepage document is what the browser parses before any shared helper.
        self.assertNotIn("api/tools.json", html)
        self.assertTrue(_bare_tools_json(html), "search still needs one lazy tools.json fetch")
        self.assertNotIn('fetch("tools.json",{cache:"no-cache"}', html)
        self.assertNotIn("cache:\"no-cache\"", html[html.find("function loadCatalog"):html.find("function loadCatalog") + 500])
        # Shared app.js must not pull the API catalog on its own.
        self.assertNotIn("api/tools.json", app)
        tasks = open(os.path.join(ROOT, "build_tasks.py"), encoding="utf-8").read()
        self.assertIn('live_metrics_script("", catalog=False)', tasks)
        site = open(os.path.join(ROOT, "build_site.py"), encoding="utf-8").read()
        self.assertIn(
            "s.replace('fetch(\"tools.json\",{cache:\"no-cache\"})', 'fetch(\"tools.json\")')",
            site,
        )
        self.assertNotIn(
            "s.replace('fetch(\"tools.json\").then', 'fetch(\"tools.json\",{cache:\"no-cache\"}).then')",
            site,
        )

    def test_new_page_stays_within_budget_and_skips_catalog_only_rows(self):
        path = os.path.join(ROOT, "new.html")
        html = open(path, encoding="utf-8").read()
        self.assertLess(os.path.getsize(path), NEW_HTML_MAX_BYTES)
        week = html.find('<h2 class="rgroup">This week')
        if week < 0:
            week = html.find('<h2 class="rgroup">Earlier this month')
        dated = html[week:] if week >= 0 else html
        cards = len(re.findall(r'<a class="card rcard"', dated))
        self.assertLessEqual(cards, NEW_DATED_CARDS_MAX)
        self.assertGreater(cards, 0)
        self.assertIn("catalog-only", html)
        self.assertIn('href="index.html#spanel"', html)
        self.assertNotIn("5,071", html)
        # A catalog-only slug from the bulk import must not be a row.
        self.assertNotIn('href="tools/marimo.html"', html)


class NewCountTest(unittest.TestCase):
    def test_week_count_skips_catalog_only(self):
        import datetime
        rows = [
            {"slug": "full", "name": "Full", "description": "A full listing.", "added": "2026-11-11", "id": 2, "seed": False, "logo": "assets/logos/orke.png"},
            {"slug": "bulk", "name": "Bulk", "description": "Catalog only.", "added": "2026-11-11", "id": 3, "seed": False, "catalog_only": True, "logo": "assets/logos/orke.png"},
            {"slug": "old", "name": "Old", "description": "Older full listing.", "added": "2026-10-01", "id": 1, "seed": False, "logo": "assets/logos/orke.png"},
        ]
        orig = build_recent.pt_today
        build_recent.pt_today = lambda: datetime.date(2026, 11, 11)
        self.addCleanup(lambda: setattr(build_recent, "pt_today", orig))
        self.assertTrue(build_recent.is_week(rows[0]))
        self.assertFalse(build_recent.is_week(rows[1]))
        shown_slugs = []
        # The page builder's cap is the constant the daily build uses.
        self.assertEqual(build_recent.NEW_CAP, 80)
        self.assertLessEqual(build_recent.NEW_CAP, 100)
        self.assertGreaterEqual(build_recent.NEW_CAP, 60)
        body, _ld = build_recent._new_body(rows)
        self.assertIn("1 full tool added", body)
        self.assertIn("1 catalog-only listing", body)
        self.assertIn('href="tools/full.html"', body)
        self.assertNotIn('href="tools/bulk.html"', body)
        self.assertNotIn("tools/old.html", body)
        shown_slugs.append("full")
        self.assertEqual(shown_slugs, ["full"])

    def test_asset_version_constant_still_exported(self):
        self.assertRegex(build_tasks.ASSET_V, r"^\d{12}$")


class RemovedToolLinkTest(unittest.TestCase):
    def test_redirected_tools_are_not_linked_from_generated_pages(self):
        bad = []
        for root in ("launches", "best"):
            base = os.path.join(ROOT, root)
            for dirpath, _dirs, files in os.walk(base):
                for fn in files:
                    if not fn.endswith(".html"):
                        continue
                    path = os.path.join(dirpath, fn)
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                    for slug in REMOVED:
                        if f"tools/{slug}.html" in text or f'data-slug="{slug}"' in text:
                            bad.append(f"{os.path.relpath(path, ROOT)} -> {slug}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
