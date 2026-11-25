#!/usr/bin/env python3
"""Indexing hygiene: sitemap seed, canonical hrefs, core sitemap selection (TASK-15, A1/A4/A8).

Pure-function tests, plus a check that a directory index is listed at its canonical URL.
No build needed. Run: python3 scripts/test_indexing_hygiene.py
"""
import json
import os
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


def test_directory_index_sitemap_loc_matches_canonical():
    """A directory index is listed at its canonical, not the index.html file path."""
    os.chdir(Path(__file__).resolve().parents[1])
    import build_prompts as bp
    canon = "https://agentscouthq.com/prompts/"
    assert bp._loc_for("prompts/") == canon
    assert bp._loc_for("prompts/index.html") == canon
    assert bp._loc_for("prompts/coding-agents.html") == "https://agentscouthq.com/prompts/coding-agents.html"
    sample = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>https://agentscouthq.com/prompts/index.html</loc><lastmod>2026-11-18</lastmod></url>\n'
        '  <url><loc>https://agentscouthq.com/tasks/index.html</loc><lastmod>2026-11-18</lastmod></url>\n'
        '</urlset>\n'
    )
    fixed = bp._align_index_html_locs(sample)
    tasks = "https://agentscouthq.com/tasks/"
    assert f"<loc>{canon}</loc>" in fixed
    assert "prompts/index.html" not in fixed
    assert f"<loc>{tasks}</loc>" in fixed
    assert "tasks/index.html" not in fixed
    assert "<lastmod>2026-11-18</lastmod>" in fixed
    assert fixed.count("<url>") == sample.count("<url>")
    both = sample.replace(
        "</urlset>\n",
        f'  <url><loc>{canon}</loc><lastmod>2026-11-18</lastmod></url>\n</urlset>\n',
    )
    deduped = bp._align_index_html_locs(both)
    assert deduped.count(f"<loc>{canon}</loc>") == 1
    assert "prompts/index.html" not in deduped
    assert deduped.count("<url>") == 2
    sm = Path("sitemap.xml").read_text(encoding="utf-8")
    assert f"<loc>{canon}</loc>" in sm
    assert "/prompts/index.html" not in sm
    assert "<loc>https://agentscouthq.com/tasks/</loc>" in sm
    assert "/tasks/index.html" not in sm

def test_homepage_filter_chips_nofollow_and_exact_counts():
    """Homepage ?cat= tiles are nofollow; VideoObject uses 6,000+/3,200+ floors; review-pages line is present."""
    import re
    import json as _json
    root = Path(__file__).resolve().parents[1]
    html = (root / "index.html").read_text(encoding="utf-8")
    tiles = list(re.finditer(r'<a class="cattile"[^>]{0,200}href="\?cat=', html))
    assert tiles, "expected homepage cattile ?cat= links"
    for m in tiles:
        assert 'rel="nofollow"' in m.group(0), m.group(0)
    title = re.search(r"<title>([^<]+)</title>", html)
    assert title and "AI Agent Tools" in title.group(1)
    assert not re.search(r"\d[\d,]*\+?\s+AI Agents", title.group(1))
    tools = _json.loads((root / "tools.json").read_text(encoding="utf-8"))
    n_tools = len(tools)
    n_mcp = sum(1 for x in tools if x.get("category") == "MCP servers")
    def _hfloor(v):
        v = int(v or 0)
        f = (v // 100) * 100
        return f if f else v
    assert f"({_hfloor(n_tools):,}+ AI agent tools & {_hfloor(n_mcp):,}+ MCP servers)" in html
    assert f"({n_tools:,}+ AI Agents" not in html
    assert "5,962" not in html
    nrev = len(re.findall(r"/tools/[^/<]+\.html", (root / "sitemap.xml").read_text(encoding="utf-8")))
    assert f"data-live-reviewed>{nrev:,}" in html
    assert "full review pages" in html



def main():
    test_sitemap_seed()
    test_canonical_hrefs()
    test_core_sitemap_selection()
    test_directory_index_sitemap_loc_matches_canonical()
    test_homepage_filter_chips_nofollow_and_exact_counts()
    print("indexing hygiene ok: sitemap seed, canonical hrefs, core sitemap selection, homepage filters and counts")


if __name__ == "__main__":
    main()
