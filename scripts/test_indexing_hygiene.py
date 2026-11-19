#!/usr/bin/env python3
"""Indexing hygiene: sitemap seed, canonical hrefs, core sitemap selection (TASK-15, A1/A4/A8).

Pure-function tests; no build needed. Run: python3 scripts/test_indexing_hygiene.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_extras as X


def test_sitemap_seed():
    assert X.SITEMAP_SEED, "SITEMAP_SEED is empty"
    for s in X.SITEMAP_SEED:
        # "" is the homepage: B + "" ends in "/" (the check is on the emitted <loc>)
        loc = X.B + s
        assert loc.endswith(".html") or loc.endswith("/"), f"sitemap seed {s!r} emits loc {loc!r}, not HTML or a directory"
        assert not s.endswith((".xml", ".txt")), f"sitemap seed {s!r} is a feed/text file"
    assert "feed.xml" not in X.SITEMAP_SEED and "llms.txt" not in X.SITEMAP_SEED
    assert "llms-full.txt" not in X.SITEMAP_SEED and "sponsor.html" in X.SITEMAP_SEED


def test_canonical_hrefs():
    cases = {
        'href="index.html"': 'href="./"',
        'href="index.html#directory"': 'href="./#directory"',
        'href="../index.html"': 'href="../"',
        'href="../index.html?uc=voice#directory"': 'href="../?uc=voice#directory"',
        'href="categories/index.html"': 'href="categories/"',
        'href="../categories/index.html"': 'href="../categories/"',
        'href="/index.html#directory"': 'href="/#directory"',
        'href="best/index.html"': 'href="best/"',
        'href="https://agentscouthq.com/index.html"': 'href="https://agentscouthq.com/index.html"',
        'href="tools/cursor.html"': 'href="tools/cursor.html"',
        # index.html must be a whole final segment: tool slugs ending in "index" are untouched
        'href="../tools/pageindex.html"': 'href="../tools/pageindex.html"',
        'href="tools/pageindex.html"': 'href="tools/pageindex.html"',
        'href="../tools/llamaindex.html"': 'href="../tools/llamaindex.html"',
        'href="../tools/productindex.html"': 'href="../tools/productindex.html"',
    }
    for src, want in cases.items():
        got = X.canonical_hrefs(f'<a {src}>x</a>')
        assert got == f"<a {want}>x</a>", f"canonical_hrefs({src!r}) = {got!r}, want {want!r}"


def test_core_sitemap_selection():
    root = Path(__file__).resolve().parents[1]
    tools = json.loads((root / "tools.json").read_text())
    urls = X.core_sitemap_urls(tools)
    assert 150 <= len(urls) <= 300, f"core sitemap has {len(urls)} candidates, want 150-300"
    assert len(urls) == len(set(urls)), "duplicate URLs in core sitemap"
    assert urls[:4] == [
        "https://agentscouthq.com/",
        "https://agentscouthq.com/about.html",
        "https://agentscouthq.com/how-it-started.html",
        "https://agentscouthq.com/mcp/status/",
    ], f"core sitemap fixed URLs wrong: {urls[:4]}"
    assert all(u.startswith("https://agentscouthq.com/") for u in urls)
    assert all(u.endswith(".html") or u.endswith("/") for u in urls)


def main():
    test_sitemap_seed()
    test_canonical_hrefs()
    test_core_sitemap_selection()
    print("indexing hygiene ok: sitemap seed, canonical hrefs, core sitemap selection")


if __name__ == "__main__":
    main()
