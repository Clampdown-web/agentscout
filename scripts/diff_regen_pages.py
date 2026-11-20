#!/usr/bin/env python3
"""Diff the guardrail-regenerated pages against main.

Date and count strings are ignored. Anything left is an unintended change:
missing share buttons, menu or footer chrome, logo alt text, title suffixes,
cache-busters, or flattened link lists.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"

PAGES = [
    "news.html",
    "sponsor.html",
    "videos/index.html",
    "leaderboard/index.html",
    "leaderboard/badges.html",
    "mcp/status/index.html",
    "prompts/index.html",
    "prompts/mcp.html",
    "prompts/coding-agents.html",
    "prompts/browser-agents.html",
]

DATE = re.compile(
    r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}"
    r"(?:, \d{1,2}:\d{2}(?::\d{2})? ?[AP]M PT)?"
    r"|\d{1,2}:\d{2}(?::\d{2})? ?[AP]M PT",
)
COUNT = re.compile(r"\d{1,3}(?:,\d{3})+")

MARKERS = (
    "sharebtn",
    "navsp",
    "Get Featured",
    "nlfoot",
    "nl-foot",
    "AI visibility check",
    "MCP server test",
    'alt=""',
    " · AgentScout",
    "og.png?v=",
    "?v=20261119-5932",
    'href="../index.html"',
    'href="../../index.html"',
    'href="../../../index.html"',
    ">Sponsored<",
    'class="b">Sponsored',
)


def main_text(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{MAIN}:{path}"], cwd=ROOT, text=True, errors="replace"
    )


def work_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def normalize(text: str) -> str:
    text = DATE.sub("«date»", text)
    text = COUNT.sub("«count»", text)
    return text


def pages() -> list[str]:
    found = list(PAGES)
    news = ROOT / "news"
    for path in sorted(news.rglob("*.html")):
        found.append(path.relative_to(ROOT).as_posix())
    return found


def main() -> int:
    problems = []
    date_only = []
    identical = []
    listed = pages()
    print(f"pages {len(listed)}")
    for rel in listed:
        try:
            old = main_text(rel)
        except subprocess.CalledProcessError:
            problems.append(f"{rel}: missing on {MAIN}")
            continue
        new = work_text(rel)
        for marker in MARKERS:
            if old.count(marker) != new.count(marker):
                problems.append(
                    f"{rel}: {marker!r} {old.count(marker)} on main, {new.count(marker)} now"
                )
        if old == new:
            identical.append(rel)
            continue
        if normalize(old) == normalize(new):
            date_only.append(rel)
            continue
        # show a short remaining mismatch
        import difflib
        left = normalize(old).splitlines() or [normalize(old)[:200]]
        right = normalize(new).splitlines() or [normalize(new)[:200]]
        diff = "".join(difflib.unified_diff(left, right, n=0, lineterm="\n")[:12])
        problems.append(f"{rel}: text differs after ignoring dates and counts\n{diff[:500]}")
    print(f"identical to main: {len(identical)}")
    print("date or count text only:")
    for rel in date_only:
        print(f"  {rel}")
    if problems:
        print(f"unintended diffs: {len(problems)}")
        for item in problems:
            print(item)
        return 1
    print("unintended diffs: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
