#!/usr/bin/env python3
"""Redirect stubs that already have a nav must keep the index.html nav.

Homepage passes insert extra header links and the link-status forwarder used
to copy that header before the nav sync removed the links. The sync then
skipped every meta-refresh page, so the extra links stayed on the redirect.
"""
from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import build_seo_new


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _index_nav():
    nav = re.search(r"<nav[^>]*>.*?</nav>", _read("index.html"), re.S)
    if not nav:
        raise AssertionError("index.html is missing nav")
    return nav.group(0)


def _with_extra_links(nav):
    old = '<a href="s/index.html">Popular lists</a>'
    extra = (
        old
        + ' · <a href="mcp/">Best MCP servers by task</a>'
        + ' · <a href="s/open-source-browser-agents.html">Free &amp; open-source browser agents</a>'
    )
    if old not in nav:
        raise AssertionError("index nav has no Popular lists link to rewrite")
    return nav.replace(old, extra, 1)


def _redirect_page(nav):
    return (
        "<!doctype html><html><head>"
        '<meta http-equiv="refresh" content="0; url=/mcp/status/">'
        "<script>location.replace(\"/mcp/status/\")</script>"
        "</head><body>"
        f"{nav}<main><p>This page moved.</p></main>"
        "</body></html>"
    )


class RedirectNavTest(unittest.TestCase):
    def test_injected_header_links_are_not_canonical(self):
        dirty = _with_extra_links(_read("index.html"))
        self.assertIn("Best MCP servers by task", dirty)
        clean = build_seo_new.canonical_index_html(dirty)
        nav = re.search(r"<nav[^>]*>.*?</nav>", clean, re.S).group(0)
        self.assertNotIn("Best MCP servers by task", nav)
        self.assertNotIn("open-source-browser-agents.html", nav)
        nested, _foot = build_seo_new.chrome_for("../", dirty)
        self.assertNotIn("Best MCP servers by task", nested)
        self.assertNotIn("open-source-browser-agents.html", nested)
        self.assertIn('href="../categories/index.html"', nested)

    def test_redirect_page_with_extra_links_fails_and_can_be_corrected(self):
        want_nav, want_foot = build_seo_new._want_chrome()
        nested = build_seo_new.prefix_rel_links(_with_extra_links(_index_nav()), "../")
        page = _redirect_page(nested)
        problems = build_seo_new.redirect_page_chrome_problems("mcp/link-status.html", page, want_nav, want_foot)
        self.assertTrue(problems)
        self.assertTrue(any("redirect nav" in line for line in problems))
        fixed = build_seo_new.apply_canonical_chrome(page, "../")
        self.assertIn('http-equiv="refresh"', fixed)
        self.assertIn("location.replace(", fixed)
        self.assertEqual(
            build_seo_new.redirect_page_chrome_problems("mcp/link-status.html", fixed, want_nav, want_foot),
            [],
        )
        self.assertNotIn("Best MCP servers by task", fixed)

    def test_location_replace_stub_is_covered(self):
        want_nav, want_foot = build_seo_new._want_chrome()
        nested = build_seo_new.prefix_rel_links(_with_extra_links(_index_nav()), "../")
        page = "<!doctype html><head><script>location.replace(\"/gone.html\")</script></head><body>" + nested + "</body>"
        problems = build_seo_new.redirect_page_chrome_problems("tasks/example.html", page, want_nav, want_foot)
        self.assertTrue(any("redirect nav" in line for line in problems))

    def test_minimal_stub_is_not_given_a_nav(self):
        games = _read("tasks/games.html")
        self.assertTrue(build_seo_new.redirect_stub(games))
        self.assertNotIn("<nav", games)
        self.assertEqual(build_seo_new.redirect_page_chrome_problems("tasks/games.html", games), [])
        self.assertEqual(build_seo_new.apply_canonical_chrome(games, "../"), games)

    def test_live_redirect_pages_match(self):
        self.assertEqual(build_seo_new.redirect_chrome_problems(), [])
        live = _read("mcp/link-status.html")
        self.assertEqual(build_seo_new.redirect_page_chrome_problems("mcp/link-status.html", live), [])


if __name__ == "__main__":
    unittest.main()
