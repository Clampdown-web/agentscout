#!/usr/bin/env python3
"""Fail when a sitewide count in the built site does not match data/site_counts.json.

Skips pagefind, data/stars, the news archive, and tools.json item records.
"Showing X of Y" is not a sitewide total. A category hub's own "N tools" is
checked against that category. "N+" is allowed when N is at most the real
total and at least 95% of it, rounded down to the nearest 50, or when N is
that total rounded down to the nearest 1,000 (the listing-pitch floor).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTS = ROOT / "data" / "site_counts.json"
PHRASE = re.compile(
    r"(?<![\d,])(\d{1,3}(?:,\d{3})+|\d+)(\+)?\s+(AI agent tools|tools in|MCP servers|categories|pages|templates)\b",
    re.I,
)
SKIP_PARTS = {"pagefind", "node_modules", ".git", "og", "preview", "bot-packages", "news"}
SKIP_FILES = {
    "tools.json",
    "tool_rich.json",
    "catalog_snapshot.json",
    "news-archive.json",
    "og_cache.json",
}
SKIP_REL = {
    "api/tools.json",
    "data/github.json",
    "data/mcp_history.json",
    "data/lastmod.json",
    "data/mcp_snapshot.json",
    "data/mcp_link_status.json",
}
SUBSET = (
    "cheat sheet",
    "we found",
    "tools in all",
    "overlapping",
    "whose listings",
    "that give",
    "that work",
    "ranked by",
    "tables started",
    "showing ",
    "govern access",
    "the top ",
    "top 100",
    "uber",
)
SITEWIDE = (
    "directory",
    "across",
    "including",
    "this site",
    "tracks",
    "indexes",
    "search all",
    "curated",
    "verified",
    "total ",
    "link-checked",
    "installable",
    "bot template",
    "pre-trained",
)


def load_counts():
    return json.loads(COUNTS.read_text(encoding="utf-8"))


def plus_ok(n, value, plus):
    if n == value:
        return True
    if not plus or value is None or n > value:
        return False
    floor = int(value * 0.95 // 50) * 50
    if n >= floor:
        return True
    thousand = (int(value) // 1000) * 1000
    return thousand > 0 and n == thousand


def _int(text):
    return int(str(text).replace(",", ""))


def accepts(kind, n, plus, ctx, counts):
    kind = kind.lower()
    freeish = "free" in ctx or "open-source" in ctx or "open source" in ctx
    if kind == "ai agent tools":
        ok = plus_ok(n, counts["tools"], plus)
        if freeish:
            ok = ok or plus_ok(n, counts["free_tools"], plus)
        return ok
    if kind == "tools in":
        ok = plus_ok(n, counts["tools"], plus)
        if freeish:
            ok = ok or plus_ok(n, counts["free_tools"], plus)
        return ok
    if kind == "mcp servers":
        return plus_ok(n, counts["mcp_servers"], plus)
    if kind == "categories":
        ok = plus_ok(n, counts["categories"], plus)
        if freeish:
            ok = ok or plus_ok(n, counts["free_categories"], plus)
        return ok
    if kind == "pages":
        return plus_ok(n, counts["pages_sitemap"], plus)
    if kind == "templates":
        return plus_ok(n, counts["bot_templates"], plus)
    return True


def sitewide_problems(text, rel, counts):
    bad = []
    for m in PHRASE.finditer(text):
        start = max(0, m.start() - 80)
        ctx = text[start:m.end() + 60].lower()
        if any(s in ctx for s in SUBSET):
            continue
        if "showing " in text[max(0, m.start() - 24):m.start()].lower():
            continue
        if not any(s in ctx for s in SITEWIDE):
            continue
        n = _int(m.group(1))
        plus = bool(m.group(2))
        if accepts(m.group(3), n, plus, ctx, counts):
            continue
        line = text.count("\n", 0, m.start()) + 1
        bad.append(f"{rel}:{line}: {m.group(0).strip()} does not match site_counts")
    return bad


def category_problems(text, rel, by_slug):
    if not rel.startswith("categories/") or not rel.endswith(".html") or rel.endswith("index.html"):
        return []
    slug = rel.split("/", 1)[1][:-5]
    expect = by_slug.get(slug)
    if expect is None:
        return []
    bad = []
    for m in re.finditer(r"Showing (\d[\d,]*) of (\d[\d,]*) tools", text):
        a, b = _int(m.group(1)), _int(m.group(2))
        if a != expect or b != expect:
            line = text.count("\n", 0, m.start()) + 1
            bad.append(f"{rel}:{line}: category hub shows {a} of {b} tools, catalog has {expect}")
    for m in re.finditer(r"out of (\d[\d,]*) tools listed", text):
        n = _int(m.group(1))
        if n != expect:
            line = text.count("\n", 0, m.start()) + 1
            bad.append(f"{rel}:{line}: category hub says {n} tools, catalog has {expect}")
    return bad


def catslug(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


FREE_RE = re.compile(r"open[- ]?source|open weights|open[- ]weight|open standard|\bfree\b|freemium", re.I)


def free_tool_items(tools):
    """Same rule as build_extras.free_tool_items. API rows have no maturity field;
    the archived/discontinued note is in the description instead."""
    def pricing(tool):
        return tool.get("pricing_detail") or tool.get("pricing") or ""
    out = []
    for tool in tools:
        pr = pricing(tool)
        status = (tool.get("maturity") or "") + " " + pr
        if not tool.get("maturity"):
            status += " " + (tool.get("description") or "")
        if FREE_RE.search(pr) and not re.search(r"discontinu|archived|shut down", status, re.I):
            out.append(tool)
    return out


def category_index(tools):
    out = {}
    for tool in tools:
        cat = tool.get("category")
        if not cat:
            continue
        slug = catslug(cat)
        out[slug] = out.get(slug, 0) + 1
    return out


def iter_built():
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for name in files:
            if name in SKIP_FILES:
                continue
            if not name.endswith((".html", ".txt", ".json")):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(ROOT).as_posix()
            if rel in SKIP_REL or rel.startswith("data/stars/") or rel.startswith("news/"):
                continue
            if rel.startswith("data/") and rel not in ("data/site_counts.json", "data/site_metrics.json"):
                continue
            yield rel, path


def stale_literals(text, rel):
    bad = []
    for needle in ("1,800+", "2,051 tools", "272 MCP"):
        if needle in text:
            line = text.count("\n", 0, text.find(needle)) + 1
            bad.append(f"{rel}:{line}: stale count {needle}")
    return bad


def catalog_only_problems(tools, counts):
    """Directory totals include catalog_only rows. Those rows stay noindex and out of the sitemap."""
    bad = []
    only = [row for row in tools if row.get("catalog_only")]
    if counts.get("tools") != len(tools):
        bad.append(f"site_counts.tools is {counts.get('tools')}, tools.json has {len(tools)}")
    if counts.get("catalog_only") != len(only):
        bad.append(f"site_counts.catalog_only is {counts.get('catalog_only')}, tools.json has {len(only)}")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").is_file() else ""
    for row in only:
        slug = row.get("slug") or ""
        if slug and f"tools/{slug}.html" in sitemap:
            bad.append(f"sitemap includes catalog_only tools/{slug}.html")
            break
    return bad


def check_tree(counts=None):
    counts = counts or load_counts()
    tools = json.loads((ROOT / "tools.json").read_text(encoding="utf-8"))
    by_slug = category_index(tools)
    bad = catalog_only_problems(tools, counts)
    for rel, path in iter_built():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        bad.extend(stale_literals(text, rel))
        bad.extend(sitewide_problems(text, rel, counts))
        bad.extend(category_problems(text, rel, by_slug))
    return bad


def recount_tools(payload):
    """tools, free, MCP from an api/tools.json or tools.json document."""
    tools = payload.get("tools") if isinstance(payload, dict) else payload
    tools = tools or []
    # api/tools.json uses "pricing" for the maker's wording (pricing_detail is folded in at export).
    free = free_tool_items(tools)
    mcp = sum(1 for x in tools if x.get("category") == "MCP servers")
    return {"tools": len(tools), "free_tools": len(free), "mcp_servers": mcp}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "AgentScout-counts-sync"})
    with urllib.request.urlopen(req, timeout=40) as res:
        return res.read().decode("utf-8", "replace")


def check_live(origin="https://agentscouthq.com"):
    """Compare the live pages with live api/metrics.json and a live tools.json recount."""
    paths = [
        "",
        "free-tools.html",
        "videos/",
        "bot-templates/",
        "sponsor.html",
        "submit.html",
        "llms.txt",
        "server.json",
        "api/metrics.json",
    ]
    bad = []
    try:
        metrics = json.loads(_get(origin + "/api/metrics.json"))
        tools_doc = json.loads(_get(origin + "/api/tools.json"))
    except Exception as exc:
        return [f"counts_sync: could not fetch live metrics or tools ({exc})"]
    recounted = recount_tools(tools_doc)
    pairs = (
        ("tools_count", "tools"),
        ("mcp_servers_count", "mcp_servers"),
    )
    for metric_key, recount_key in pairs:
        if int(metrics.get(metric_key) or 0) != recounted[recount_key]:
            bad.append(
                f"counts_sync: live api/metrics.json {metric_key}={metrics.get(metric_key)} "
                f"but live api/tools.json recount is {recounted[recount_key]}"
            )
    expected = {
        "tools": recounted["tools"],
        "free_tools": recounted["free_tools"],
        "free_categories": metrics.get("categories_count"),
        "mcp_servers": recounted["mcp_servers"],
        "categories": int(metrics.get("categories_count") or 0),
        "pages_sitemap": int(metrics.get("indexed_pages_count") or metrics.get("pages_count") or 0),
        "bot_templates": int(metrics.get("templates_count") or 0),
    }
    # Bot-template total is the row count on the live hub when metrics has no templates_count.
    if not expected["bot_templates"]:
        try:
            hub = _get(origin + "/bot-templates/")
            expected["bot_templates"] = len(re.findall(r'<li class="bt-row"', hub))
        except Exception as exc:
            bad.append(f"counts_sync: could not count live bot templates ({exc})")
    # Free-category total is whatever the free-tools page states next to the free-tool total.
    try:
        free_page = _get(origin + "/free-tools.html")
    except Exception:
        free_page = ""
    m = re.search(r"([\d,]+) free and open-source AI agent tools in (\d+) categories", free_page)
    if m:
        if _int(m.group(1)) != recounted["free_tools"]:
            bad.append(
                f"counts_sync: live free-tools.html says {_int(m.group(1))} free tools, recount is {recounted['free_tools']}"
            )
        expected["free_categories"] = int(m.group(2))
    for path in paths:
        url = origin + "/" + path
        try:
            body = free_page if path == "free-tools.html" else _get(url)
        except Exception as exc:
            bad.append(f"counts_sync: {url} ({exc})")
            continue
        rel = path or "index.html"
        for line in sitewide_problems(body, "live/" + rel, expected):
            bad.append("counts_sync: " + line)
    if int(metrics.get("tools_count") or 0) != recounted["tools"]:
        pass
    if recounted["free_tools"] and free_page and str(recounted["free_tools"]) not in free_page and f"{recounted['free_tools']:,}" not in free_page:
        bad.append(f"counts_sync: live free-tools.html does not show {recounted['free_tools']} free tools")
    return bad


def main():
    if not COUNTS.is_file():
        print("check_counts: data/site_counts.json is missing")
        return 1
    bad = check_tree()
    if bad:
        print(f"check_counts: {len(bad)} mismatch(es)")
        for line in bad[:80]:
            print(line)
        if len(bad) > 80:
            print(f"... {len(bad) - 80} more")
        return 1
    counts = load_counts()
    print(
        "check_counts: 0 mismatches "
        f"(tools={counts['tools']} free={counts['free_tools']} mcp={counts['mcp_servers']} "
        f"categories={counts['categories']} pages={counts['pages_sitemap']} templates={counts['bot_templates']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
