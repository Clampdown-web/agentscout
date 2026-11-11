#!/usr/bin/env python3
"""A generated page must not state a directory tool or MCP total other than api/metrics.json.

A different number is allowed when the same sentence is a dated snapshot
("as of Nov 9, 2026", "on Oct 22, 2026") or it also names the live total
("154 listings" next to "323 MCP servers"). GitHub star cells must not sit
where a reader can take them as a tool count ("2,316 ToolsPad").
"""
from __future__ import annotations

import html as html_lib
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "api" / "metrics.json"

SKIP_DIRS = {
    ".git", "node_modules", "pagefind", "assets", "og", "preview",
    "bot-packages", "tools", "news", "bot-store", "bot-templates", "data",
}
SKIP_FILES = {"tools.json", "tool_rich.json", "news-archive.json", "news-history.json"}

COUNT = r"(\d{1,3}(?:,\d{3})+|\d+)"
DATE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
    re.I,
)
# Directory claims only. "All 11 tools" on a role page is that role's list, not the catalog.
LEAD_COUNT = re.compile(
    rf"(?i)(?<![\d,]){COUNT}(\+)?\s+(AI agent tools|tools|MCP servers)\b"
)
THESE_MCP = re.compile(rf"\bThese {COUNT} MCP servers\b", re.I)
WHOSE_MCP = re.compile(rf"\b{COUNT} MCP servers whose\b", re.I)
STARTED = re.compile(rf"\b(?:Tables )?started with {COUNT} MCP servers\b", re.I)
# A star count glued to the next row's name (ToolHive's 2,316, then ToolsPad).
STAR_NAMED_TOOL = re.compile(r"(?<![\d,])(\d{1,3}(?:,\d{3})+)\s+Tools[A-Za-z]")
CATALOG_PHRASE = re.compile(
    rf"(?i)\b(?:including|lists|tracks|part of|directory of)\s+{COUNT}(\+)?\s+"
    rf"(AI agent tools|tools|MCP servers)\b"
)


def _int(text: str) -> int:
    return int(str(text).replace(",", ""))


def _fmt(n: int) -> str:
    return f"{n:,}"


def plus_ok(n: int, value: int, plus: bool) -> bool:
    if n == value:
        return True
    if not plus or n > value:
        return False
    floor = int(value * 0.95 // 50) * 50
    if n >= floor:
        return True
    # Same rule as scripts/check_counts.py: a listing pitch may use the nearest-1,000 floor.
    thousand = (int(value) // 1000) * 1000
    return thousand > 0 and n == thousand


def visible(html: str) -> str:
    """Drop script and style, including end tags with whitespace or attributes (``</script >``)."""
    text = re.sub(r"(?is)<script\b.*?</script\b[^>]*>", " ", html)
    text = re.sub(r"(?is)<style\b.*?</style\b[^>]*>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def clauses(text: str) -> list[str]:
    """Sentences. A date used only as a list label ('Oct 22, 2026: …') does not date the claim."""
    out = []
    for part in re.split(r"(?<=[.!?])\s+", text):
        part = part.strip()
        if not part:
            continue
        labeled = re.match(
            r"^(?:[A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})\s*:\s*(.+)$",
            part,
        )
        out.append(labeled.group(1) if labeled else part)
    return out


def kind_of(label: str) -> str:
    return "mcp" if "mcp" in label.lower() else "tools"


def allowed(n: int, kind: str, plus: bool, sentence: str, tools: int, mcp: int) -> bool:
    value = mcp if kind == "mcp" else tools
    if plus_ok(n, value, plus):
        return True
    if DATE.search(sentence):
        return True
    if _fmt(value) in sentence or re.search(rf"(?<![\d,]){value}(?![\d,])", sentence):
        return True
    return False


def lead_bits(rel: str, raw: str) -> list[tuple[str, str]]:
    bits = []
    if rel.endswith(".html"):
        for pat, name in (
            (r'<meta name="description" content="([^"]*)"', "meta"),
            (r'<meta property="og:description" content="([^"]*)"', "og"),
            (r'<meta name="twitter:description" content="([^"]*)"', "twitter"),
            (r'<p class="lede"[^>]*>(.*?)</p>', "lede"),
        ):
            for m in re.finditer(pat, raw, flags=re.I | re.S):
                bits.append((name, visible(m.group(1))))
    return bits


def problems_in(rel: str, raw: str, tools: int, mcp: int) -> list[str]:
    bad = []
    text = raw if not rel.endswith(".html") else visible(raw)
    for sentence in clauses(text):
        for m in STAR_NAMED_TOOL.finditer(sentence):
            n = _int(m.group(1))
            window = sentence[max(0, m.start() - 24):m.end() + 12].lower()
            if n != tools and "star" not in window:
                bad.append(f"{rel}: {m.group(0)} reads as a tool count (directory is {tools:,})")
        for rx in (THESE_MCP, WHOSE_MCP, STARTED):
            for m in rx.finditer(sentence):
                n = _int(m.group(1))
                if not allowed(n, "mcp", False, sentence, tools, mcp):
                    bad.append(f"{rel}: {m.group(0)} is not {mcp:,} MCP servers and is not dated")
        for m in CATALOG_PHRASE.finditer(sentence):
            n = _int(m.group(1))
            plus = bool(m.group(2))
            kind = kind_of(m.group(3))
            if not allowed(n, kind, plus, sentence, tools, mcp):
                bad.append(f"{rel}: {m.group(0).strip()} does not match api/metrics.json")
    for where, bit in lead_bits(rel, raw):
        for sentence in clauses(bit):
            # Meta and lede: an MCP total with no date and no live total beside it.
            if not re.search(r"\bMCP servers\b", sentence, re.I):
                continue
            for m in LEAD_COUNT.finditer(sentence):
                if "mcp" not in m.group(3).lower():
                    continue
                n = _int(m.group(1))
                plus = bool(m.group(2))
                if allowed(n, "mcp", plus, sentence, tools, mcp):
                    continue
                bad.append(f"{rel} {where}: {m.group(0).strip()} does not match api/metrics.json")
    return bad


def iter_pages():
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name in SKIP_FILES:
                continue
            if not name.endswith((".html", ".txt", ".json")):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("api/") and rel != "api/sections.json":
                continue
            if not rel.endswith((".html", ".txt")) and rel != "api/sections.json":
                continue
            yield rel, path.read_text(encoding="utf-8", errors="ignore")


# Visible catalog counts (tools, categories, MCP, stars). A 4-digit year is left alone.
_COUNT_BEFORE = re.compile(
    r"(?<![\w.$])(\d{4,})(?![\d,])"
    r"(?=(?:</(?:b|span|strong)>)?\s*\+?\s+"
    r"(?:tools?|MCPs?\b|listings|pricing\b|link-checked|servers\b|of\b|[Bb]est\b|live\b|checked\b|repos\b|AI\b|in the MCP))"
)
_COUNT_OF = re.compile(r"(?<![\w.$])of\s+(\d{4,})(?![\d,])")
_COUNT_PAREN = re.compile(r"\((\d{4,})\)")


def _year_number(n: int) -> bool:
    return 1900 <= n <= 2099


def count_token_spans(text: str) -> list[tuple[int, int, str]]:
    """Unformatted count tokens of 1000 or more. Years in 1900-2099 are not counts."""
    spans = set()
    for rx in (_COUNT_BEFORE, _COUNT_OF, _COUNT_PAREN):
        for m in rx.finditer(text):
            raw = m.group(1)
            n = int(raw)
            if n < 1000 or _year_number(n):
                continue
            spans.add((m.start(1), m.end(1), raw))
    return sorted(spans)


def insert_count_commas(text: str) -> str:
    """Comma-format count tokens, leaving tool-card blurbs alone."""
    parts = re.split(r'(<p class="hook">.*?</p>)', text, flags=re.S)
    out = []
    for part in parts:
        if part.startswith('<p class="hook">'):
            out.append(part)
            continue
        hits = count_token_spans(part)
        if not hits:
            out.append(part)
            continue
        buf = part
        for start, end, raw in reversed(hits):
            buf = buf[:start] + f"{int(raw):,}" + buf[end:]
        out.append(buf)
    return "".join(out)


def visible_count_problems(rel: str, html: str) -> list[str]:
    """Title, meta, and visible copy. Scripts, styles, and tool blurbs are not copy."""
    bad = []
    title = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    bits = [("title", html_lib.unescape(title.group(1)))] if title else []
    for pat, name in (
        (r'<meta name="description" content="([^"]*)"', "meta"),
        (r'<meta property="og:description" content="([^"]*)"', "og"),
        (r'<meta name="twitter:description" content="([^"]*)"', "twitter"),
    ):
        for m in re.finditer(pat, html, flags=re.I):
            bits.append((name, html_lib.unescape(m.group(1))))
    body = re.sub(r'(?is)<p class="hook">.*?</p>', " ", html)
    body = visible(body)
    bits.append(("body", html_lib.unescape(body)))
    for where, text in bits:
        for _start, _end, raw in count_token_spans(text):
            ctx_at = text.find(raw)
            ctx = text[max(0, ctx_at - 28):ctx_at + len(raw) + 28].strip()
            bad.append(f"{rel} {where}: {raw} in {ctx}")
    return bad


def catalog_problems(tools: int | None = None, mcp: int | None = None) -> list[str]:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    tools = int(metrics["tools_count"] if tools is None else tools)
    mcp = int(metrics["mcp_servers_count"] if mcp is None else mcp)
    bad = []
    for rel, raw in iter_pages():
        bad.extend(problems_in(rel, raw, tools, mcp))
    return bad


class CatalogCountTests(unittest.TestCase):
    def test_visible_strips_script_and_style_end_tags_with_whitespace(self):
        html = (
            "<p>2,407 tools</p>"
            "<script type=\"text/javascript\">2,316 tools</script >"
            "<style type=\"text/css\">233 MCP servers</style >"
        )
        text = visible(html)
        self.assertIn("2,407 tools", text)
        self.assertNotIn("2,316", text)
        self.assertNotIn("233", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("<style", text)

    def test_generated_pages_match_metrics(self):
        bad = catalog_problems()
        self.assertFalse(bad, "\n".join(bad[:40]))

    def test_count_token_spans_ignore_years_prices_and_formatted_numbers(self):
        self.assertEqual(count_token_spans("Browse 5716 AI agent tools"), [(7, 11, "5716")])
        self.assertEqual(count_token_spans("40 categories, 5,716 tools."), [])
        self.assertEqual(count_token_spans("Top 15 of 1344 by stars."), [(10, 14, "1344")])
        self.assertEqual(count_token_spans("MCP servers (2026)"), [])
        self.assertEqual(count_token_spans("Fast-Track $5716"), [])
        self.assertEqual(count_token_spans("Showing 3177 of 3177 tools"), [(8, 12, "3177"), (16, 20, "3177")])

    def test_public_pages_use_thousands_separators(self):
        bad = []
        for rel in ("index.html", "categories/index.html", "categories/mcp-servers.html"):
            raw = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
            bad.extend(visible_count_problems(rel, raw))
        js = (ROOT / "catfilter.js").read_text(encoding="utf-8")
        if 'toLocaleString("en-US")' not in js and "toLocaleString('en-US')" not in js:
            bad.append("catfilter.js does not format counts with toLocaleString('en-US')")
        if 'Showing "+n+' in js or "Showing \"+n+" in js:
            bad.append("catfilter.js still writes a raw Showing count")
        self.assertFalse(bad, "\n".join(bad[:40]))

    def test_generators_read_metrics_and_date_snapshots(self):
        aicite = (ROOT / "build_aicite.py").read_text(encoding="utf-8")
        extras = (ROOT / "build_extras.py").read_text(encoding="utf-8")
        self.assertIn("metrics_catalog()", aicite)
        self.assertIn("GitHub stars", aicite)
        self.assertIn("dated_start", aicite)
        self.assertIn("metrics_catalog()", extras)
        self.assertIn("mcp_client_copy", extras)
        self.assertNotIn(
            "These {len(named)} MCP servers",
            extras,
        )


if __name__ == "__main__":
    unittest.main()
