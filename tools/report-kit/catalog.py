"""Prices and Stripe links for the paid reports.

data/mcp_test_report.json prices the MCP server test and the bundle.
data/ai_visibility_check.json prices the AI visibility check. sell is
"intro" or "full". The page and the product feed use that choice.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRICES = ROOT / "data" / "mcp_test_report.json"
VISIBILITY = ROOT / "data" / "ai_visibility_check.json"
MCP_PAGE = "https://agentscouthq.com/mcp-test-report.html"
VIS_PAGE = "https://agentscouthq.com/ai-visibility-check.html"
ORDER = ("mcp-server-test", "ai-visibility", "bundle")


def load_prices(path: Path | None = None) -> dict:
    return json.loads((path or PRICES).read_text(encoding="utf-8"))


def load_visibility(path: Path | None = None) -> dict:
    return json.loads((path or VISIBILITY).read_text(encoding="utf-8"))


def selling(product: dict, doc: dict) -> tuple[int, str]:
    """The price and checkout URL the site should use right now."""
    if doc.get("sell") == "full":
        return int(product["price"]), product["checkout_url"]
    return int(product["intro"]), product["intro_checkout_url"]


def _deliverables(product_id: str) -> list[str]:
    if product_id == "ai-visibility":
        return [
            "Private noindex report page and PDF",
            "One free retest or fix check of the same site within 30 days after delivery",
        ]
    return [
        "Private noindex report page and PDF",
        "Tested by AgentScout badge for the dated result",
        "One free retest or fix check of the same server or site within 30 days after delivery",
    ]


def catalog_entries(doc: dict | None = None) -> list[dict]:
    """Report rows for api/products.json. The visibility check comes from its own price file."""
    doc = doc or load_prices()
    chosen: dict[str, tuple[dict, dict]] = {}
    for product in doc["products"]:
        chosen[product["id"]] = (product, doc)
    if VISIBILITY.is_file():
        visibility = load_visibility()
        for product in visibility["products"]:
            if product["id"] == "ai-visibility" and product.get("in_catalog"):
                chosen[product["id"]] = (product, visibility)
    rows = []
    for product_id in ORDER:
        pair = chosen.get(product_id)
        if not pair:
            continue
        product, source = pair
        if not product.get("in_catalog"):
            continue
        price, url = selling(product, source)
        page = VIS_PAGE if product_id == "ai-visibility" else MCP_PAGE
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
            "badge": "Intro" if source.get("sell") != "full" else "",
            "checkout_url": url,
            "checkout_url_regular": product["checkout_url"],
            "intro_checkout_url": product["intro_checkout_url"],
            "page_url": page,
            "description": product["blurb"] + " " + source["intro"]["note"],
            "deliverables": _deliverables(product_id),
        })
    return rows
