"""Prices and Stripe links for the paid reports.

data/mcp_test_report.json is the only place those numbers and payment links
live. sell is "intro" or "full". The page and the product feed use that choice.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRICES = ROOT / "data" / "mcp_test_report.json"


def load_prices(path: Path | None = None) -> dict:
    return json.loads((path or PRICES).read_text(encoding="utf-8"))


def selling(product: dict, doc: dict) -> tuple[int, str]:
    """The price and checkout URL the site should use right now."""
    if doc.get("sell") == "full":
        return int(product["price"]), product["checkout_url"]
    return int(product["intro"]), product["intro_checkout_url"]


def catalog_entries(doc: dict | None = None) -> list[dict]:
    """MCP report and bundle rows for api/products.json. The visibility check stays off until its page exists."""
    doc = doc or load_prices()
    rows = []
    for product in doc["products"]:
        if not product.get("in_catalog"):
            continue
        price, url = selling(product, doc)
        rows.append({
            "id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "category": "report",
            "price_usd": price,
            "regular_price_usd": int(product["price"]),
            "intro_price_usd": int(product["intro"]),
            "billing_model": "one_time",
            "availability": "in_stock",
            "badge": "Intro" if doc.get("sell") != "full" else "",
            "checkout_url": url,
            "checkout_url_regular": product["checkout_url"],
            "intro_checkout_url": product["intro_checkout_url"],
            "page_url": "https://agentscouthq.com/mcp-test-report.html",
            "description": product["blurb"] + " " + doc["intro"]["note"],
            "deliverables": [
                "Private noindex report page and PDF",
                "Tested by AgentScout badge for the dated result",
                "One free retest or fix check of the same server or site within 30 days after delivery",
            ],
        })
    return rows
