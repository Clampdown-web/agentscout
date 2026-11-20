#!/usr/bin/env python3
"""The MCP pricing page meta stays about pricing."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "mcp" / "pricing.html"


def description(html: str) -> str:
    match = re.search(r'<meta\b[^>]*name=["\']description["\'][^>]*>', html, re.I)
    if not match:
        match = re.search(r'<meta\b[^>]*content=["\'][^"\']*["\'][^>]*name=["\']description["\'][^>]*>', html, re.I)
    if not match:
        return ""
    content = re.search(r'content=["\']([^"\']*)["\']', match.group(0))
    return content.group(1) if content else ""


class McpPricingMetaTest(unittest.TestCase):
    def test_meta_starts_with_mcp_server_pricing(self):
        text = description(PAGE.read_text(encoding="utf-8"))
        self.assertTrue(text.lower().startswith("mcp server pricing"), text)
        self.assertNotIn("checked servers live", text.lower())


if __name__ == "__main__":
    unittest.main()
