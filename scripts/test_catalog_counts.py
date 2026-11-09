#!/usr/bin/env python3
"""A generated page must not state a directory tool or MCP total other than api/metrics.json.

A different number is allowed when the same sentence is a dated snapshot
("as of Nov 9, 2026", "on Oct 22, 2026") or it also names the live total
("154 listings" next to "323 MCP servers"). GitHub star cells must not sit
where a reader can take them as a tool count ("2,316 ToolsPad").
"""
from __future__ import annotations

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
    return n >= floor


def visible(html: str) -> str:
    text = re.sub(r"(?is)<script\b.*?</script>", " ", html)
    text = re.sub(r"(?is)<style\b.*?</style>", " ", text)
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


def catalog_problems(tools: int | None = None, mcp: int | None = None) -> list[str]:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    tools = int(metrics["tools_count"] if tools is None else tools)
    mcp = int(metrics["mcp_servers_count"] if mcp is None else mcp)
    bad = []
    for rel, raw in iter_pages():
        bad.extend(problems_in(rel, raw, tools, mcp))
    return bad


class CatalogCountTests(unittest.TestCase):
    def test_generated_pages_match_metrics(self):
        bad = catalog_problems()
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
