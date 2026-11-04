#!/usr/bin/env python3
"""Address checks for the MCP link checker and the tool ingest fetches."""
import ipaddress
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

import check_mcp_links
import add_tools


class PublicAddressTest(unittest.TestCase):
    def test_shared_address_space_is_not_global(self):
        ip = ipaddress.ip_address("100.64.0.1")
        self.assertIs(ip.is_private, False)
        self.assertIs(ip.is_global, False)
        self.assertIs(check_mcp_links.public("http://cgnat.example/", resolve=lambda host: ["100.64.0.1"]), False)
        self.assertIs(check_mcp_links.public("https://ok.example/path", resolve=lambda host: ["8.8.8.8"]), True)
        self.assertIs(check_mcp_links.public("http://mix.example/", resolve=lambda host: ["8.8.8.8", "10.0.0.1"]), False)
        self.assertIs(check_mcp_links.public("http://multi.example/", resolve=lambda host: ["224.0.0.1"]), False)
        self.assertIs(check_mcp_links.public("http://none.example/", resolve=lambda host: []), False)

    def test_homepage_and_icon_fetches_stop_at_public(self):
        calls = []

        def fake_get(url, headers=None, timeout=None, allow_redirects=None):
            calls.append(url)
            return Response(url)

        add_tools.requests.get = fake_get
        add_tools.public = lambda url: "127.0.0.1" not in url and "169.254" not in url
        self.assertIsNone(add_tools.getimg("http://127.0.0.1/icon.png"))
        self.assertEqual(calls, [])
        page = add_tools.open_public("https://example.com/icon.png", 5)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(calls, ["https://example.com/icon.png"])
        calls.clear()
        redirected = add_tools.open_public("https://example.com/start", 5)
        self.assertIsNone(redirected)
        self.assertEqual(calls, ["https://example.com/start"])


class Response:
    def __init__(self, url):
        self.url = url
        self.status_code = 302 if url.endswith("/start") else 200
        self.headers = {"Location": "http://127.0.0.1/secret"} if self.status_code == 302 else {}
        self.content = b"\x89PNG\r\n"
        self.is_redirect = self.status_code == 302


class ReviewStarTest(unittest.TestCase):
    def test_star_markup_is_numeric(self):
        import build_reviews
        raw = "<img src=x onerror=alert(1)>"
        html = build_reviews.stars(raw)
        self.assertNotIn("<img", html)
        self.assertIn("--r:0", html)
        section = build_reviews.section(
            {"name": "Widget", "slug": "widget"},
            {"count": 1, "avg": 4.5, "reviews": [{"stars": raw, "name": "A", "text": "ok", "ts": 0}]},
            "1",
        )
        self.assertNotIn("<img", section)
        self.assertIn(">0 out of 5 stars<", section)
        self.assertIn("--r:4.5", section)


if __name__ == "__main__":
    unittest.main()
