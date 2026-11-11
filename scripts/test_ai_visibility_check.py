#!/usr/bin/env python3
"""AI visibility check: intro prices on the page, full price only in the data file, private sample."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "report-kit"))

import catalog  # noqa: E402

PRICES = json.loads((ROOT / "data" / "ai_visibility_check.json").read_text(encoding="utf-8"))
SAMPLE = PRICES["sample_slug"]
FULL = "https://buy.stripe.com/8x26oI6T15hl2WF7rte7m0j"
INTRO = "https://buy.stripe.com/14A4gAdhpeRV2WFaDFe7m0i"
BUNDLE = "https://buy.stripe.com/bJe8wQ2CL39d0Ox8vxe7m0k"


class VisibilityPriceTest(unittest.TestCase):
    def test_sell_flag_and_sample_slug(self):
        self.assertEqual(PRICES["sell"], "intro")
        self.assertGreaterEqual(len(SAMPLE), 24)
        self.assertNotIn("token", SAMPLE.lower())
        ids = [row["id"] for row in PRICES["products"]]
        self.assertEqual(ids, ["ai-visibility", "mcp-server-test", "bundle"])
        vis = next(row for row in PRICES["products"] if row["id"] == "ai-visibility")
        self.assertEqual(vis["intro_checkout_url"], INTRO)
        self.assertEqual(vis["checkout_url"], FULL)
        self.assertEqual(vis["intro"], 79)
        self.assertEqual(vis["price"], 99)
        self.assertTrue(vis["on_page"])
        self.assertTrue(vis["in_catalog"])

    def test_page_shows_intro_buttons_only(self):
        page = (ROOT / "ai-visibility-check.html").read_text(encoding="utf-8")
        shown = [row for row in PRICES["products"] if row.get("on_page")]
        hidden = [row for row in PRICES["products"] if not row.get("on_page")]
        self.assertEqual([row["id"] for row in shown], ["ai-visibility", "bundle"])
        for row in shown:
            price, url = catalog.selling(row, PRICES)
            self.assertIn(url, page)
            self.assertIn(f">${price}<", page)
            self.assertIn(f">${row['price']}<", page)
            self.assertNotIn(row["checkout_url"], page)
        for row in hidden:
            self.assertNotIn(row["intro_checkout_url"], page)
            self.assertNotIn(row["checkout_url"], page)
        self.assertIn(INTRO, page)
        self.assertIn(BUNDLE, page)
        self.assertNotIn(FULL, page)
        self.assertEqual(page.count('class="paynote"'), len(shown))
        self.assertIn('href="refunds.html"', page)
        self.assertIn("Questions? Email support@agentscouthq.com", page)
        self.assertIn('href="mcp-test-report.html"', page)
        self.assertIn("G-TGDXK5F13D", page)
        self.assertIn("default-src 'self'", page)
        self.assertNotIn("<form", page.lower())
        self.assertNotIn("noindex", page[:2500])
        self.assertIn("styles.css?v=", page)
        self.assertIn("ai-visibility-check.css?v=", page)
        self.assertIn("ChatGPT", page)
        self.assertIn("Perplexity", page)
        self.assertIn("Google AI Overviews", page)

    def test_private_sample_is_noindex_and_absent_from_the_sitemap(self):
        report = ROOT / "r" / SAMPLE / "index.html"
        pdf = ROOT / "r" / SAMPLE / "report.pdf"
        self.assertTrue(report.is_file())
        self.assertGreater(pdf.stat().st_size, 1000)
        html = report.read_text(encoding="utf-8")
        self.assertIn('content="noindex, nofollow"', html)
        self.assertIn('http-equiv="Content-Security-Policy"', html)
        self.assertIn("default-src 'self'", html)
        self.assertIn("#0A0A0B", (ROOT / "assets" / "ai-visibility-report" / "report.css").read_text(encoding="utf-8"))
        self.assertIn("#FF8A3D", html)
        self.assertEqual(len(re.findall(r'class="sheet\b', html)), 9)
        self.assertIn("G-TGDXK5F13D", html)
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn(f"/r/{SAMPLE}", sitemap)
        self.assertNotIn("/r/", sitemap)
        self.assertIn("https://agentscouthq.com/ai-visibility-check.html", sitemap)
        kit = (ROOT / "tools" / "report-kit" / "ai-visibility" / "sample.html").read_text(encoding="utf-8")
        self.assertIn('content="noindex, nofollow"', kit)

    def test_catalog_lists_the_check_at_the_intro_price(self):
        products = json.loads((ROOT / "api" / "products.json").read_text(encoding="utf-8"))
        row = next(item for item in products["reports"] if item["id"] == "ai-visibility")
        self.assertEqual(row["price_usd"], 79)
        self.assertEqual(row["checkout_url"], INTRO)
        self.assertEqual(row["checkout_url_regular"], FULL)
        self.assertEqual(row["page_url"], "https://agentscouthq.com/ai-visibility-check.html")
        acp = json.loads((ROOT / ".well-known" / "acp.json").read_text(encoding="utf-8"))
        self.assertEqual(products, acp)

    def test_nav_links_the_check_beside_the_mcp_test(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="mcp-test-report.html">MCP server test</a><a href="ai-visibility-check.html">AI visibility check</a>', home)
        tool = (ROOT / "tools" / "agent.html").read_text(encoding="utf-8")
        self.assertIn('href="../mcp-test-report.html">MCP server test</a><a href="../ai-visibility-check.html">AI visibility check</a>', tool)
        refunds = (ROOT / "refunds.html").read_text(encoding="utf-8")
        self.assertIn("MCP server test reports and AI visibility checks", refunds)
        self.assertIn('href="ai-visibility-check.html">AI visibility check</a>', refunds)


if __name__ == "__main__":
    unittest.main()
