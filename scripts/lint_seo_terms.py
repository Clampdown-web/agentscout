#!/usr/bin/env python3
"""Fail a rewrite that drops product, client, category, protocol, or official URL terms from a listing's title or meta.

Owner rule (27 Nov 2026, America/Los_Angeles): listing copy may be rewritten in
plain language, but the HTML <title> and meta description must keep product
names, client names (Claude Code, Coinbase, and the like), category terms
(MCP server, x402), protocol names (streamable HTTP, stdio), and official
MCP or docs URLs that were already in the title or meta on the base commit
(origin/main, or BASE_SHA).

Removals of those same terms from the page's technical body (main content
outside the lede) are flagged, but they do not fail the check by themselves.

Diff-aware: only tools/*.html pages added or changed versus the base
commit are scanned. data/seo_overrides.json is also compared when it changes.

  python3 scripts/lint_seo_terms.py
  python3 scripts/lint_seo_terms.py --base origin/main --head HEAD

Guardrails CI calls failures() from scripts/guardrails/pr_check.py.
The daily listing-copy cleanup batch should run this after
scripts/apply_seo_overrides.py.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_DEFAULT = Path(__file__).resolve().parents[1]

# Longest first so "Claude Code" wins over "Claude".
PROTECTED_TERMS = (
    "Claude Code",
    "Claude",
    "Coinbase",
    "Cursor",
    "Codex",
    "OpenAI",
    "Anthropic",
    "Lovable",
    "idealo",
    "Firecracker",
    "MiniMax",
    "FFmpeg",
    "Robinhood",
    "Uniswap",
    "Outlook",
    "iCloud",
    "Fastmail",
    "CalDAV",
    "Gmail",
    "Model Context Protocol",
    "MCP servers",
    "MCP server",
    "streamable HTTP",
    "streamable-HTTP",
    "stdio",
    "OAuth",
    "x402",
    "HTTP PUT",
    "GET /market",
    "GET /trust",
)

# Official MCP / docs hosts and paths that matter even if not in the generic list.
RE_OFFICIAL_URL = re.compile(
    r"""
    (?:https?://)?
    (?:www\.)?
    (
      [a-z0-9-]+(?:\.[a-z0-9-]+)+
      (?:/(?:mcp|api/mcp|docs)(?:/[^\s<\"',;)]*)?)?
    )
    """,
    re.I | re.X,
)

RE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
RE_META_DESC = re.compile(r'<meta name="description" content="([^"]*)"')
RE_MAIN = re.compile(r"<main\b[^>]*>(.*?)</main>", re.S | re.I)
RE_LEDE = re.compile(r'<p class="lede">.*?</p>', re.S | re.I)
RE_TAGS = re.compile(r"<[^>]+>")


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "diff.renames=false", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _blob(repo: Path, sha: str | None, path: str) -> str | None:
    if not sha:
        return None
    result = _git(repo, "cat-file", "-p", f"{sha}:{path}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _changed_paths(repo: Path, base: str, head: str) -> list[str]:
    result = _git(repo, "diff", "--name-only", f"{base}...{head}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def unescape_html(text: str) -> str:
    return html.unescape(text or "")


def page_title(document: str) -> str:
    match = RE_TITLE.search(document or "")
    return unescape_html(match.group(1)).strip() if match else ""


def page_meta(document: str) -> str:
    match = RE_META_DESC.search(document or "")
    return unescape_html(match.group(1)).strip() if match else ""


def head_text(document: str) -> str:
    return " ".join(part for part in (page_title(document), page_meta(document)) if part)


def technical_text(document: str) -> str:
    """Main content minus the lede, used only for flags."""
    match = RE_MAIN.search(document or "")
    chunk = match.group(1) if match else (document or "")
    chunk = RE_LEDE.sub(" ", chunk)
    chunk = RE_TAGS.sub(" ", chunk)
    return unescape_html(" ".join(chunk.split()))


def _term_present(text: str, term: str) -> bool:
    if not text or not term:
        return False
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.I) is not None


def official_urls(text: str) -> list[str]:
    found: list[str] = []
    for match in RE_OFFICIAL_URL.finditer(text or ""):
        value = match.group(1).rstrip(").,;:")
        # Skip generic leftover hosts that are not product/docs/MCP paths.
        host = value.split("/", 1)[0].lower()
        if host in {"github.com", "agentscouthq.com", "www.github.com"}:
            continue
        if value.lower() not in {item.lower() for item in found}:
            found.append(value)
    return found


def protected_in(text: str) -> list[str]:
    found: list[str] = []
    for term in PROTECTED_TERMS:
        if _term_present(text, term) and term.lower() not in {item.lower() for item in found}:
            found.append(term)
    for url in official_urls(text):
        if url.lower() not in {item.lower() for item in found}:
            found.append(url)
    return found


def missing_terms(old_text: str, new_text: str) -> list[str]:
    missing: list[str] = []
    for term in protected_in(old_text):
        if not _term_present(new_text, term) and not any(
            item.lower() == term.lower() for item in official_urls(new_text)
        ):
            missing.append(term)
    return missing


def product_name_from_tools(tools_json: str | None, slug: str) -> str:
    if not tools_json:
        return ""
    try:
        data = json.loads(tools_json)
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, list):
        return ""
    for item in data:
        if isinstance(item, dict) and item.get("slug") == slug:
            return str(item.get("name") or "").strip()
    return ""


def slug_from_tool_path(path: str) -> str | None:
    rel = path.replace("\\", "/")
    if rel.startswith("tools/") and rel.endswith(".html") and rel.count("/") == 1:
        return rel[6:-5]
    return None


def _load_overrides(text: str | None) -> dict[str, tuple[str, str]]:
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, tuple[str, str]] = {}
    for path, pair in data.items():
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            out[str(path)] = (str(pair[0] or ""), str(pair[1] or ""))
    return out


def failures(repo: Path, base: str, head: str) -> list[str]:
    """Return hard-fail messages for title/meta term removals."""
    messages, _flags = check(repo, base, head)
    return messages


def flags(repo: Path, base: str, head: str) -> list[str]:
    """Return technical-section term-removal flags (non-failing)."""
    _messages, flagged = check(repo, base, head)
    return flagged


def check(repo: Path, base: str, head: str) -> tuple[list[str], list[str]]:
    changed = _changed_paths(repo, base, head)
    tools_head = _blob(repo, head, "tools.json")
    messages: list[str] = []
    flagged: list[str] = []

    paths = [path for path in changed if slug_from_tool_path(path)]
    # If seo_overrides.json changed, also inspect those tool pages even if HTML is unchanged.
    if "data/seo_overrides.json" in changed:
        old_over = _load_overrides(_blob(repo, base, "data/seo_overrides.json"))
        new_over = _load_overrides(_blob(repo, head, "data/seo_overrides.json"))
        for path in set(old_over) | set(new_over):
            if slug_from_tool_path(path) and path not in paths:
                # Only when the override text itself changed, or the page exists at head.
                if old_over.get(path) != new_over.get(path):
                    paths.append(path)

    seen: set[str] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        slug = slug_from_tool_path(path)
        if not slug:
            continue
        old_html = _blob(repo, base, path) or ""
        new_html = _blob(repo, head, path)
        if new_html is None:
            continue
        if not old_html:
            # New listings have no base title/meta to compare. The guard is for
            # removals from copy that already existed on the base commit.
            continue

        old_head = head_text(old_html)
        new_head = head_text(new_html)
        missing = missing_terms(old_head, new_head)
        name = product_name_from_tools(tools_head, slug) or product_name_from_tools(
            _blob(repo, base, "tools.json"), slug
        )
        if name and name.lower() not in page_title(new_html).lower():
            missing = list(dict.fromkeys(missing + [name]))
        if missing:
            messages.append(
                f"Listing '{slug}' title or meta description dropped protected term(s) "
                f"{', '.join(repr(term) for term in missing)} compared with the base commit. "
                f"Keep product names, client names, category terms, protocol names, and official "
                f"MCP or docs URLs in the HTML title and meta. New title: {page_title(new_html)!r}. "
                f"New meta: {page_meta(new_html)!r}."
            )

        body_missing = missing_terms(technical_text(old_html), technical_text(new_html))
        # Terms already reported as title/meta failures are the same story; still flag body loss.
        if body_missing:
            flagged.append(
                f"FLAG: listing '{slug}' technical section dropped protected term(s) "
                f"{', '.join(repr(term) for term in body_missing)}. Leave them in the technical "
                f"section or FAQ if they are still true; do not only keep them in the head."
            )
    return messages, flagged


def _default_base(repo: Path) -> str:
    env = os.environ.get("BASE_SHA", "").strip()
    if env:
        return env
    result = _git(repo, "rev-parse", "--verify", "origin/main", check=False)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    result = _git(repo, "rev-parse", "--verify", "main", check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _default_head() -> str:
    return os.environ.get("HEAD_SHA", "").strip() or "HEAD"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("REPO", str(REPO_DEFAULT)))
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    base = args.base.strip() or _default_base(repo)
    head = args.head.strip() or _default_head()
    if not base:
        print("No base commit. Pass --base origin/main or set BASE_SHA.")
        return 1
    messages, flagged = check(repo, base, head)
    for flag in flagged:
        print(flag)
        print()
    if messages:
        print("SEO term lint failed.\n")
        for number, message in enumerate(messages, 1):
            print(f"{number}. {message}\n")
        return 1
    print("SEO term lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
