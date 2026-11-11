#!/usr/bin/env python3
"""MCP test report product: prices, private sample, and no checkout except the intro Stripe links."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "report-kit"))
sys.path.insert(0, str(ROOT / "tools" / "report-kit" / "harness"))

import catalog  # noqa: E402
from redact import redact_obj, redact_text  # noqa: E402

PRICES = json.loads((ROOT / "data" / "mcp_test_report.json").read_text(encoding="utf-8"))
TOKEN = PRICES["sample_slug"]


class PriceConfigTest(unittest.TestCase):
    def test_sell_flag_selects_the_intro_links(self):
        self.assertEqual(PRICES["sell"], "intro")
        self.assertGreaterEqual(len(TOKEN), 24)
        ids = [row["id"] for row in PRICES["products"]]
        self.assertEqual(ids, ["mcp-server-test", "ai-visibility", "bundle"])
        for row in PRICES["products"]:
            self.assertTrue(row["checkout_url"].startswith("https://buy.stripe.com/"))
            self.assertTrue(row["intro_checkout_url"].startswith("https://buy.stripe.com/"))
            self.assertNotEqual(row["checkout_url"], row["intro_checkout_url"])

    def test_product_page_uses_intro_buttons_and_the_pay_note(self):
        page = (ROOT / "mcp-test-report.html").read_text(encoding="utf-8")
        shown = [row for row in PRICES["products"] if row.get("on_page")]
        hidden = [row for row in PRICES["products"] if not row.get("on_page")]
        self.assertEqual([row["id"] for row in shown], ["mcp-server-test", "bundle"])
        for row in shown:
            price, url = catalog.selling(row, PRICES)
            self.assertIn(url, page)
            self.assertIn(f">${price}<", page)
            self.assertIn(f">${row['price']}<", page)
            self.assertNotIn(row["checkout_url"], page)
        for row in hidden:
            self.assertNotIn(row["intro_checkout_url"], page)
            self.assertNotIn(row["checkout_url"], page)
        self.assertEqual(page.count('class="paynote"'), len(shown))
        self.assertIn("Refund policy", page)
        self.assertIn('href="refunds.html"', page)
        self.assertIn("Questions? Email support@agentscouthq.com", page)
        self.assertNotIn("<form", page.lower())
        self.assertNotIn("noindex", page[:2500])
        self.assertIn("styles.css?v=", page)
        self.assertIn("mcp-test-report.css?v=", page)

    def test_private_sample_is_noindex_and_absent_from_the_sitemap(self):
        report = ROOT / "r" / TOKEN / "index.html"
        pdf = ROOT / "r" / TOKEN / "report.pdf"
        self.assertTrue(report.is_file())
        self.assertTrue(pdf.is_file())
        html = report.read_text(encoding="utf-8")
        self.assertIn('content="noindex, nofollow"', html)
        self.assertIn('http-equiv="Content-Security-Policy"', html)
        self.assertIn("default-src 'self'", html)
        self.assertEqual(len(re.findall(r'class="sheet\b', html)), 9)
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn(f"/r/{TOKEN}", sitemap)
        self.assertNotIn("/r/", sitemap)
        self.assertIn("https://agentscouthq.com/mcp-test-report.html", sitemap)
        headers = (ROOT / "_headers").read_text(encoding="utf-8")
        self.assertIn("X-Robots-Tag: noindex, nofollow", headers)
        self.assertIn("Content-Security-Policy:", headers)
        # Public pages may link the two samples. They may not link any other /r/ path.
        visibility = json.loads((ROOT / "data" / "ai_visibility_check.json").read_text(encoding="utf-8"))
        linked = set(re.findall(r'href="(?:\.\./)*r/([^"/]+)/', "\n".join(
            p.read_text(encoding="utf-8", errors="ignore")
            for p in ROOT.glob("*.html")
        )))
        self.assertEqual(linked, {TOKEN, visibility["sample_slug"]})

    def test_catalog_lists_the_report_and_the_bundle_at_the_intro_price(self):
        products = json.loads((ROOT / "api" / "products.json").read_text(encoding="utf-8"))
        acp = json.loads((ROOT / ".well-known" / "acp.json").read_text(encoding="utf-8"))
        snap = json.loads((ROOT / "cloudflare-mcp-worker" / "products_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(products, acp)
        self.assertEqual(products, snap)
        rows = {row["id"]: row for row in products["reports"]}
        self.assertEqual(set(rows), {"mcp-server-test", "ai-visibility", "bundle"})
        for row in catalog.catalog_entries(PRICES):
            self.assertEqual(rows[row["id"]]["checkout_url"], row["checkout_url"])
            self.assertEqual(rows[row["id"]]["price_usd"], row["price_usd"])

    def test_refunds_keep_the_eu_line_and_name_the_reports(self):
        text = (ROOT / "refunds.html").read_text(encoding="utf-8")
        self.assertIn(
            "By the pay buttons, you agree that delivery starts right away. If you are in the EU or the UK, that agreement ends the 14-day right to cancel.",
            text,
        )
        self.assertIn("MCP server test reports and AI visibility checks", text)
        self.assertIn("What is the refund for an MCP server test report, an AI visibility check, or the bundle?", text)
        for row in PRICES["products"]:
            self.assertIn(f'${row["price"]}', text)
            self.assertIn(f'${row["intro"]}', text)

    def test_harness_redacts_session_tokens(self):
        # A fixed stand-in, not a credential. The redactor must remove it before print or save.
        marker = "example-session-value"
        payload = {
            "response_headers": {"mcp-session-id": marker},
            "raw_preview": f"hello {marker} bearer {marker}",
            "note": "Authorization: Bearer " + marker,
        }
        cleaned = redact_obj(payload, (marker,))
        blob = json.dumps(cleaned)
        self.assertNotIn(marker, blob)
        self.assertIn("[redacted]", blob)
        self.assertNotIn(marker, redact_text(f"session={marker}", (marker,)))


if __name__ == "__main__":
    unittest.main()
