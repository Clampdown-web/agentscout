#!/usr/bin/env python3
"""Grouped nav must load the nav stylesheet, and the retired SSE path must stay gone.

A page with class="sitenav" has to reference styles.css at the current ASSET_V
(or home-mobile.css, which carries the same nav rules). Any built page, generator,
or published manifest that still names that path fails.
"""
from __future__ import annotations

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_tasks  # noqa: E402

ASSET = build_tasks.ASSET_V
MARKERS = ("nav.sitenav .navburger", "nav.sitenav.is-open .navlinks", "summary::-webkit-details-marker")
DESKTOP_BAR = "nav.sitenav .navburger,nav.sitenav .nav-open{display:none}"
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
    if DESKTOP_BAR in css:
        bad.append("styles.css still hides the hamburger at desktop width")
    if DESKTOP_BAR in home:
        bad.append("home-mobile.css still hides the hamburger at desktop width")
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
            if "navburger" in text or 'id="nav-open"' in text:
                if not re.search(r'<script\b[^>]*\bsrc="[^"]*app\.js\?v=' + re.escape(ASSET) + r'"', text):
                    bad.append(f"{rel} has the hamburger without a real app.js?v={ASSET} tag")
            bad.extend(_duplicate_menu_hrefs(rel, text))
        if rel == "index.html":
            if f"home-mobile.css?v={ASSET}" not in text:
                bad.append(f"index.html home-mobile.css is not ?v={ASSET}")
            if 'var urls=["app.js' in text or re.search(r'var urls=\[[^\]]*"app\.js\?v=', text):
                bad.append("index.html still defers app.js in the after-paint list")
            svc = text.find('id="services"')
            directory = text.find('id="directory"')
            nl = text.find('id="nlblock"')
            if svc < 0 or directory < 0 or not (svc < directory):
                bad.append("index.html Services block is not above the directory")
            if nl < 0 or svc > nl:
                bad.append("index.html moved the weekly signup")
            if text.count('id="services"') != 1:
                bad.append("index.html Services block is duplicated")
            if 'class="svc-back"' not in text:
                bad.append("index.html is missing the footer link back to Services")
        if rel == "sponsor.html" and "api/tools.json" in text:
            bad.append("sponsor.html still fetches api/tools.json")
        if rel.endswith(".tpl") and 'class="sitenav"' in text:
            bad.extend(_duplicate_menu_hrefs(rel, text))
    return bad


def _menu_href(href):
    href = href.split("#", 1)[0].split("?", 1)[0]
    if href.endswith("index.html"):
        href = href[: -len("index.html")]
    return href.rstrip("/")


def _duplicate_menu_hrefs(rel, text):
    """Same destination twice inside one dropdown section."""
    bad = []
    nav = re.search(r'<nav class="sitenav".*?</nav>', text, re.S)
    if not nav:
        return bad
    for group in re.finditer(
        r'<details class="navgroup[^"]*"><summary>([^<]*)</summary><div class="navpanel">(.*?)</div></details>',
        nav.group(0),
    ):
        seen = {}
        for href in re.findall(r'href="([^"]+)"', group.group(2)):
            key = _menu_href(href)
            seen[key] = seen.get(key, 0) + 1
        dups = [href for href, count in seen.items() if count > 1]
        if dups:
            bad.append(f"{rel} {group.group(1)} menu repeats {', '.join(dups)}")
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
