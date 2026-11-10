#!/usr/bin/env python3
"""Every production page loads consent.js and paints the privacy banner first.

Redirect stubs, email fragments, and the OG card stay exempt.
"""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_tasks  # noqa: E402


def _pages():
    skip = {".git", "node_modules", "pagefind", "preview"}
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        for name in files:
            if name.endswith(".html"):
                yield os.path.relpath(os.path.join(dirpath, name), ROOT)


class ConsentPagesTest(unittest.TestCase):
    def test_defer_before_src_still_gets_consent_and_the_banner(self):
        sample = '<html><body><script defer src="app.js?v=1"></script></body></html>'
        out = build_tasks.ensure_shared_scripts("submit.html", sample, "")
        self.assertIn('<script defer src="consent.js?v=', out)
        self.assertIn('<script defer src="track.js?v=', out)
        self.assertLess(out.find("consent.js"), out.find("track.js"))
        self.assertIn('class="as-bar"', out)
        self.assertIn('href="privacy.html"', out)
        self.assertNotIn('class="as-note"', out)

    def test_attribute_order_src_before_defer(self):
        sample = '<html><body><script src="../app.js?v=9" defer></script></body></html>'
        out = build_tasks.ensure_shared_scripts("tools/zed.html", sample, "../")
        self.assertIn('<script defer src="../consent.js?v=', out)
        self.assertIn('href="../privacy.html"', out)

    def test_every_production_page_includes_consent_and_the_banner(self):
        missing = []
        for rel in _pages():
            path = os.path.join(ROOT, rel)
            text = open(path, encoding="utf-8", errors="replace").read()
            if build_tasks.shared_scripts_exempt(rel, text):
                continue
            if rel == "index.html" and "consent.js?v=" in text and 'class="as-bar"' in text:
                continue
            if "consent.js" not in text or 'class="as-bar"' not in text:
                missing.append(rel)
        self.assertEqual(missing, [], "\n".join(missing[:30]))


if __name__ == "__main__":
    unittest.main()
