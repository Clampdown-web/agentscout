#!/usr/bin/env python3
"""Share cards are 1200x630, dark, and point at absolute cache-busted URLs."""
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_counts  # noqa: E402
import build_og  # noqa: E402
from PIL import Image  # noqa: E402


class OgCardTest(unittest.TestCase):
    def test_tool_card_is_dark_and_small(self):
        png = build_og.render(
            "AI agent tool",
            "MagenticLite",
            "Browser agent from Microsoft Research.",
            "Browser/computer use · Open source",
            os.path.join(ROOT, "assets/logos/magentic-ui.png"),
        )
        self.assertLess(len(png), 300_000)
        im = Image.open(io.BytesIO(png)).convert("RGB")
        self.assertEqual(im.size, (1200, 630))
        r, g, b = im.getpixel((12, 40))
        self.assertLess(r + g + b, 80)
        self.assertEqual(im.getpixel((20, 3)), (147, 147, 255))
        self.assertEqual(im.getpixel((900, 3)), (45, 226, 230))
        bright = 0
        for y in range(190, 280, 3):
            for x in range(230, 900, 6):
                R, G, B = im.getpixel((x, y))
                if R + G + B > 640:
                    bright += 1
        self.assertGreater(bright, 15)

    def test_meta_is_absolute_large_summary(self):
        html = (
            '<meta property="og:site_name" content="AgentScout">'
            '<meta property="og:image" content="https://agentscouthq.com/og.png">'
            '<meta name="twitter:card" content="summary">'
        )
        url = "https://agentscouthq.com/og/tools/magentic-ui.png?v=abc123def4"
        out = build_og.apply_meta(html, url, "MagenticLite, on AgentScout")
        self.assertIn(f'content="{url}"', out)
        self.assertIn('og:image:width" content="1200"', out)
        self.assertIn('og:image:height" content="630"', out)
        self.assertIn('og:image:alt" content="MagenticLite, on AgentScout"', out)
        self.assertIn('twitter:image" content="' + url + '"', out)
        self.assertIn('twitter:card" content="summary_large_image"', out)
        self.assertEqual(out.count("twitter:image"), 1)
        again = build_og.apply_meta(out, url, "MagenticLite, on AgentScout")
        self.assertEqual(again, out)

    def test_static_cards_keep_generic_counts(self):
        self.assertEqual(build_counts.pitch_tools_label(5716), "5,000+ AI agent tools")
        self.assertEqual(build_counts.pitch_mcp_label(3177), "3,000+ MCP servers")
        blob = " ".join(str(part) for row in build_og.static_specs() for part in row)
        self.assertIn("The AI agent tools actually worth trying.", blob)
        self.assertIn("5,000+ AI agent tools", blob)
        self.assertIn("3,000+ MCP servers", blob)
        self.assertNotIn("5,716", blob)
        self.assertNotIn("3,177", blob)


if __name__ == "__main__":
    unittest.main()
