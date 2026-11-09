#!/usr/bin/env python3
"""Grouped nav must load the nav stylesheet, and the retired SSE path must stay gone.

A page with class="sitenav" has to reference styles.css at the current ASSET_V
(or home-mobile.css, which carries the same nav rules). Any built page, generator,
or published manifest that still names that path fails.
"""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_tasks  # noqa: E402

ASSET = build_tasks.ASSET_V
MARKERS = ("nav.sitenav .nav-open", "summary::-webkit-details-marker")
SKIP_DIRS = {".git", "node_modules", "preview", "assets", "__pycache__"}
DEAD = "/mcp/" + "sse"


def _walk():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            yield os.path.relpath(os.path.join(root, fn), ROOT)


def problems():
    bad = []
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    home = open(os.path.join(ROOT, "home-mobile.css"), encoding="utf-8").read()
    for mark in MARKERS:
        if mark not in css:
            bad.append(f"styles.css missing {mark}")
        if mark not in home:
            bad.append(f"home-mobile.css missing {mark}")
    for rel in _walk():
        if not rel.endswith((".html", ".py", ".js", ".mjs", ".json", ".txt", ".yaml", ".yml", ".md")):
            continue
        path = os.path.join(ROOT, rel)
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if DEAD in text:
            bad.append(f"{rel} contains {DEAD}")
        if rel.endswith(".html") and 'class="sitenav"' in text:
            stamped = f"styles.css?v={ASSET}" in text
            homepage_css = "home-mobile.css" in text
            if not stamped and not homepage_css:
                bad.append(f"{rel} has the grouped nav without styles.css?v={ASSET}")
    return bad


class NavCssTest(unittest.TestCase):
    def test_nav_stylesheet_and_live_mcp_endpoint(self):
        bad = problems()
        self.assertEqual(bad, [], "\n".join(bad[:30]))


if __name__ == "__main__":
    bad = problems()
    print(f"nav/endpoint check: {len(bad)} problems")
    for line in bad[:30]:
        print(" ", line)
    sys.exit(1 if bad else 0)
