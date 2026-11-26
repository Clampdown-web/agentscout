#!/usr/bin/env python3
"""Start here is a compact chip row on the homepage and the two hubs only."""
from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_tasks  # noqa: E402

HOME_HREFS = (
    "mcp/status/",
    "mcp/?sort=responds",
    "best/best-mcp-servers-2026.html",
    "guides/",
    "guides/how-to-automate-workflows-with-ai-agents.html",
    "guides/how-to-crawl-websites-for-ai-agents.html",
)
MCP_HREFS = (
    "status/",
    "?sort=responds",
    "../best/best-mcp-servers-2026.html",
    "../guides/",
    "../guides/how-to-automate-workflows-with-ai-agents.html",
    "../guides/how-to-crawl-websites-for-ai-agents.html",
)
BEST_HREFS = (
    "../mcp/status/",
    "../mcp/?sort=responds",
    "../mcp/",
    "best-mcp-servers-2026.html",
    "../guides/",
    "../guides/how-to-automate-workflows-with-ai-agents.html",
    "../guides/how-to-crawl-websites-for-ai-agents.html",
)


def _block(text):
    m = re.search(r"<!--start-here-->.*?<!--/start-here-->", text, re.S)
    return m.group(0) if m else ""


class StartHereTests(unittest.TestCase):
    def test_helper_targets_and_idempotent_slots(self):
        home = build_tasks.start_here_html("home")
        for href in HOME_HREFS:
            self.assertIn(f'href="{href}"', home)
        self.assertNotIn("nofollow", home)
        self.assertNotIn("<nav", home)
        self.assertNotIn("guide-list", home)
        self.assertIn(">Start here</h2>", home)
        sample = "<!--vs:home-->card<!--/vs:home--></div></header><section id=\"services\" class=\"hsec\">"
        once = build_tasks.ensure_start_here(sample, "home")
        self.assertLess(once.find("<!--/vs:home-->"), once.find("<!--start-here-->"))
        self.assertLess(once.find("<!--/start-here-->"), once.find("</header>"))
        self.assertLess(once.find("</header>"), once.find('id="services"'))
        self.assertNotIn("start-here", once.split("<!--/vs:home-->", 1)[0])
        self.assertEqual(build_tasks.ensure_start_here(once, "home"), once)
        mcp = '<p class="lede">Lede.</p><!--vs:list-->v<!--/vs:list--><p>Jump to</p><select data-responds-sort></select>'
        mcp_out = build_tasks.ensure_start_here(mcp, "mcp")
        self.assertLess(mcp_out.find("<!--/start-here-->"), mcp_out.find("<!--vs:list-->"))
        self.assertLess(mcp_out.find("<!--/start-here-->"), mcp_out.find("Jump to"))
        self.assertIn("data-responds-sort", mcp_out)
        for href in MCP_HREFS:
            self.assertIn(f'href="{href}"', _block(mcp_out))
        best = '<p class="lede">Lede.</p><!--qa:bestidx-->qa<!--/qa:bestidx--><ul class="guide-list"></ul>'
        best_out = build_tasks.ensure_start_here(best, "best")
        self.assertLess(best_out.find("<!--/qa:bestidx-->"), best_out.find("<!--start-here-->"))
        self.assertLess(best_out.find("<!--/start-here-->"), best_out.find("guide-list"))
        for href in BEST_HREFS:
            self.assertIn(f'href="{href}"', _block(best_out))

    def test_built_pages_and_generators(self):
        home = Path(ROOT, "index.html").read_text(encoding="utf-8")
        mcp = Path(ROOT, "mcp", "index.html").read_text(encoding="utf-8")
        best = Path(ROOT, "best", "index.html").read_text(encoding="utf-8")
        home_block = _block(home)
        mcp_block = _block(mcp)
        best_block = _block(best)
        self.assertTrue(home_block and mcp_block and best_block)
        for href in HOME_HREFS:
            self.assertIn(f'href="{href}"', home_block)
        for href in MCP_HREFS:
            self.assertIn(f'href="{href}"', mcp_block)
        for href in BEST_HREFS:
            self.assertIn(f'href="{href}"', best_block)
        for block in (home_block, mcp_block, best_block):
            self.assertNotIn("nofollow", block)
            self.assertEqual(block.count("<!--start-here-->"), 1)
        self.assertLess(home.find("<!--/vs:home-->"), home.find("<!--start-here-->"))
        self.assertLess(home.find("<!--/start-here-->"), home.find("</header>"))
        self.assertLess(home.find("</header>"), home.find('id="services"'))
        self.assertIn('</header><section id="services"', home)
        self.assertLess(mcp.find('class="lede"'), mcp.find("<!--start-here-->"))
        self.assertLess(mcp.find("<!--/start-here-->"), mcp.find("<!--vs:list-->"))
        self.assertLess(mcp.find("<!--/start-here-->"), mcp.find(">Jump to<"))
        self.assertIn("data-responds-sort", mcp)
        self.assertNotIn("data-responds-sort", mcp_block)
        self.assertLess(best.find("<!--/qa:bestidx-->"), best.find("<!--start-here-->"))
        self.assertLess(best.find("<!--/start-here-->"), best.find('class="guide-list"'))
        for rel, src in (
            ("build_status.py", "ensure_start_here"),
            ("build_mcp_tasks.py", 'start_here_html("mcp")'),
            ("build_best.py", 'start_here_html("best")'),
            ("build_tasks.py", 'ensure_start_here(s, "home")'),
        ):
            text = Path(ROOT, rel).read_text(encoding="utf-8")
            self.assertIn(src, text, rel)
        css = Path(ROOT, "styles.css").read_text(encoding="utf-8")
        self.assertIn(".start-here-chips{display:flex;flex-wrap:wrap", css)
        self.assertIn(".start-here-chips a:hover{border-color:var(--accent)", css)
        for folder, keep in (("mcp", "index.html"), ("best", "index.html")):
            base = os.path.join(ROOT, folder)
            for name in os.listdir(base):
                if not name.endswith(".html"):
                    continue
                text = Path(base, name).read_text(encoding="utf-8")
                if name == keep:
                    self.assertIn("<!--start-here-->", text, name)
                else:
                    self.assertNotIn("<!--start-here-->", text, f"{folder}/{name}")
        for rel in (
            "mcp/status/index.html",
            "guides/index.html",
            "guides/how-to-automate-workflows-with-ai-agents.html",
            "guides/how-to-crawl-websites-for-ai-agents.html",
            "best/best-mcp-servers-2026.html",
        ):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


if __name__ == "__main__":
    unittest.main()
