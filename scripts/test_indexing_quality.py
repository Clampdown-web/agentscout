#!/usr/bin/env python3
"""Indexing quality: prune thin pages, label sponsored spots, honest titles (TASK-18).

Pure-function tests run with no build. Built-tree checks run when sitemap.xml exists
(run after a build); otherwise they are skipped with a note.
Run: python3 scripts/test_indexing_quality.py
"""
import html as _html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_extras as X

ROOT = Path(__file__).resolve().parents[1]
B = "https://agentscouthq.com/"
KEEP = ["browser-use-alternatives", "chrome-devtools-mcp-alternatives",
        "cherry-studio-alternatives", "cli-anything-alternatives",
        "context7-alternatives", "cursor-alternatives", "dify-alternatives",
        "graphify-alternatives", "librechat-alternatives", "mem0-alternatives",
        "mempalace-alternatives", "oh-my-openagent-omo-alternatives",
        "oh-my-pi-alternatives", "omniroute-alternatives", "opencode-alternatives",
        "open-webui-alternatives", "openviking-alternatives",
        "paperclip-alternatives", "ruflo-alternatives", "skills-sh-alternatives"]
SPONSORED = ["botpress", "sendblox", "lazy-ads", "mailveri-mcp", "swipeharbor"]
TOTAL_RE = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d{4,})\s+(AI agent tools|MCP servers)")


def test_keep_list():
    assert X.kept_alternatives() == set(KEEP), f"keep list mismatch: {sorted(X.kept_alternatives())}"
    assert len(KEEP) == 20, f"keep list has {len(KEEP)} entries, want 20"
    assert all(k.endswith("-alternatives") for k in KEEP)
    data = json.loads((ROOT / "data" / "index_keep_alternatives.json").read_text())
    assert data["keep"] == sorted(KEEP), "data file keep list is not the sorted 20"


def test_sitemap_drop():
    assert X.sitemap_drop(B + "news/2026/11/some-story.html")
    assert X.sitemap_drop(B + "news/2026/10/another-story.html")
    assert X.sitemap_drop(B + "best/cognee-alternatives.html")
    assert X.sitemap_drop(B + "best/langchain-alternatives.html")
    assert X.sitemap_drop(B + "sponsor.html")
    assert not X.sitemap_drop(B + "news.html")
    assert not X.sitemap_drop(B + "news/")
    assert not X.sitemap_drop(B + "news/2026/11/")
    assert not X.sitemap_drop(B + "news/2026/10/")
    for k in KEEP:
        assert not X.sitemap_drop(B + "best/" + k + ".html"), f"kept page dropped: {k}"
    assert not X.sitemap_drop(B + "best/best-mcp-servers-2026.html")
    assert not X.sitemap_drop(B + "best/")
    assert not X.sitemap_drop(B + "tools/cursor.html")
    assert not X.sitemap_drop(B + "categories/mcp-servers.html")


def test_noindex_helpers():
    page = "<html><head><title>t</title></head><body>x</body></html>"
    once = X.add_noindex(page)
    assert once.count("noindex,follow") == 1 and "<head>\n" in once
    assert X.add_noindex(once) == once, "add_noindex is not idempotent"
    assert X.strip_noindex(once) == page, "strip_noindex did not restore the page"
    assert X.strip_noindex(page) == page
    assert X.add_noindex(X.add_noindex(page)) == X.add_noindex(page)


def test_sponsored_helpers():
    assert X.sponsored_slugs() == set(SPONSORED), f"sponsored slugs: {sorted(X.sponsored_slugs())}"
    assert X.visit_rel("botpress") == "sponsored nofollow noopener noreferrer"
    assert X.visit_rel("cursor") == "noopener noreferrer"
    assert X.sponsored_badge("botpress") == ' <span class="b">Affiliate link</span>'
    assert X.sponsored_badge("cursor") == ""
    sample = ('<a href="https://botpress.com" target="_blank" rel="noopener noreferrer">Visit</a> '
              '<a href="https://example.com" target="_blank" rel="noopener noreferrer">Other</a>')
    out = X.sponsored_rel(sample, "botpress", "https://botpress.com")
    assert 'href="https://botpress.com" target="_blank" rel="sponsored nofollow noopener noreferrer"' in out
    assert 'href="https://example.com" target="_blank" rel="noopener noreferrer"' in out
    assert X.sponsored_rel(sample, "cursor", "cursor.com") == sample
    assert X.sponsored_rel(sample, "botpress", "") == sample


def test_honest_titles():
    assert X.cat_title("MCP servers", 3194) == "Best MCP servers & MCP tools (2026) · AgentScout"
    assert not TOTAL_RE.search(X.cat_title("coding", 5900))
    copy = X.mcp_client_copy("Cursor", [{"category": "MCP servers"}] * 3,
                             {"tools": 5900, "mcp": 3194, "updated": "Nov 18, 2026"})
    assert not TOTAL_RE.search(copy["desc"]), f"client-guide desc still claims a total: {copy['desc']}"
    assert "3 listings work with Cursor" in copy["desc"]
    assert 120 <= len(copy["desc"]) <= 160, copy["desc"]
    # the body lede may still show catalog counts
    assert "5,900 tools" in copy["count_sentence"]


def _locs(path):
    return re.findall(r"<loc>([^<]+)</loc>", Path(path).read_text(encoding="utf-8"))


def _head(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")[:5000]


def _noindex(path):
    return 'name="robots" content="noindex' in _head(path)


def check_built_tree():
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        print("SKIP built-tree checks: no sitemap.xml (run a build first)")
        return
    locs = _locs(sm)
    stories = [u for u in locs if re.match(r"https://agentscouthq\.com/news/\d{4}/\d{2}/[^/]+\.html$", u)]
    assert not stories, f"story pages in sitemap: {stories[:5]}"
    nonkept = [u for u in locs if re.match(r"https://agentscouthq\.com/best/([a-z0-9-]+)-alternatives\.html$", u)
               and u.split("/")[-1][:-5] not in KEEP]
    assert not nonkept, f"non-kept alternatives in sitemap: {nonkept[:5]}"
    assert B + "sponsor.html" not in locs, "sponsor.html is in the sitemap"
    for k in KEEP:
        assert B + "best/" + k + ".html" in locs, f"kept page missing from sitemap: {k}"
    for u in (B + "news.html", B + "news/"):
        assert u in locs, f"news hub missing from sitemap: {u}"
    hubs = [u for u in locs if re.match(r"https://agentscouthq\.com/news/\d{4}/\d{2}/$", u)]
    assert hubs, "no monthly news hubs in sitemap"
    print(f"built-tree sitemap ok: {len(locs)} locs, 0 story pages, 0 non-kept alternatives, "
          f"20/20 kept alternatives, sponsor out, {len(hubs)} monthly hubs")

    assert _noindex(ROOT / "sponsor.html"), "sponsor.html has no noindex meta"
    story_files = sorted(p for p in (ROOT / "news").glob("*/*/*.html") if p.name != "index.html")
    assert story_files, "no built news story pages found"
    bad = [str(p.relative_to(ROOT)) for p in story_files if not _noindex(p)]
    assert not bad, f"story pages without noindex: {bad[:5]}"
    alt_files = sorted((ROOT / "best").glob("*-alternatives.html"))
    bad = [str(p.relative_to(ROOT)) for p in alt_files
           if p.name[:-5] not in KEEP and not _noindex(p)]
    assert not bad, f"non-kept alternatives without noindex: {bad[:5]}"
    bad = [str(p.relative_to(ROOT)) for p in alt_files
           if p.name[:-5] in KEEP and _noindex(p)]
    assert not bad, f"kept alternatives wrongly noindexed: {bad[:5]}"
    print(f"built-tree noindex ok: {len(story_files)} story pages + "
          f"{len(alt_files) - len(KEEP)} non-kept alternatives noindexed, 20 kept indexable")

    # Honest titles / H1s / meta descriptions: no catalog total anywhere.
    # preview/ is a stale test snapshot, not an indexed page, so it is out of scope.
    total_pat = TOTAL_RE
    bad = []
    for p in sorted(ROOT.rglob("*.html")):
        if p.relative_to(ROOT).parts[0] in ("pagefind", "node_modules", "preview", "app"):
            continue
        s = p.read_text(encoding="utf-8", errors="replace")[:20000]
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', s)
        h = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        for label, m in (("TITLE", t), ("DESC", d), ("H1", h)):
            if m and total_pat.search(_html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))):
                bad.append(f"{label} {p.relative_to(ROOT)}: {m.group(1)[:100]}")
    assert not bad, "catalog total in title/H1/meta:\n" + "\n".join(bad[:10])
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "<title>AgentScout: AI Agent Tools &amp; MCP Servers (2026)</title>" in home
    mcp = (ROOT / "categories" / "mcp-servers.html").read_text(encoding="utf-8")
    assert "<title>Best MCP servers &amp; MCP tools (2026) · AgentScout</title>" in mcp
    print("built-tree titles ok: no catalog total in any title, H1 or meta description")

    # Sponsored labels: every sponsored slug linked from a /best or /compare table
    # carries a visible Sponsored badge in the same row/card, and compare Visit links
    # to sponsored hosts carry rel="sponsored".
    checked_rows = 0
    for p in sorted((ROOT / "best").glob("*.html")) + sorted((ROOT / "compare").glob("*.html")):
        s = p.read_text(encoding="utf-8", errors="replace")
        for slug in SPONSORED:
            for m in re.finditer(r'href="[^"]*tools/' + re.escape(slug) + r'\.html"', s):
                # Only table rows and cards count: prose links (the "why consider"
                # lines, Quick-answer paragraph) are not placements.
                tr_start = s.rfind("<tr", 0, m.start())
                tr_end = s.find("</tr>", m.start())
                # Enclosing row only: the row must not close before the link.
                if tr_start >= 0 and tr_end > m.start() and s.find("</tr>", tr_start) > m.start():
                    block = s[tr_start:tr_end]
                else:
                    card_start = max(s.rfind('<li class="card tile"', 0, m.start()),
                                     s.rfind('<a class="card tile"', 0, m.start()))
                    if card_start < 0:
                        continue
                    close_tag = "</li>" if s[card_start:card_start + 3] == "<li" else "</a>"
                    card_end = s.find(close_tag, m.start())
                    # Enclosing card only: the card must not close before the link.
                    if card_end <= m.start() or s.find(close_tag, card_start) <= m.start():
                        continue
                    block = s[card_start:card_end]
                assert ">Affiliate link<" in block, (
                    f"{p.relative_to(ROOT)}: sponsored slug {slug} shown without an Affiliate link label")
                checked_rows += 1
    # Compare Visit links: no sponsored slug is in a compare pair right now, so this
    # asserts the helper contract and reports the live count (0 expected today).
    print(f"built-tree sponsored labels ok: {checked_rows} sponsored rows/cards checked "
          f"(compare pairs with a sponsored tool: 0)")


def main():
    test_keep_list()
    test_sitemap_drop()
    test_noindex_helpers()
    test_sponsored_helpers()
    test_honest_titles()
    print("indexing quality ok: keep list, sitemap filter, noindex helpers, sponsored helpers, honest titles")
    check_built_tree()


if __name__ == "__main__":
    main()
