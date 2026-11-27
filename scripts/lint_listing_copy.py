#!/usr/bin/env python3
"""Fail a pull request that adds or changes listing copy in a bot-like voice.

Owner rule (27 Nov 2026, America/Los_Angeles): every new listing — scraped
morning-build discovery, paid $15/$49/$99, and free maker submissions — must
read like natural human writing. This lint is enforcement for *new or edited*
copy only. Existing backlog listings are left alone until the owner says to
rewrite them.

Checked fields:
  tools.json            description, pricing_detail
  tool_rich.json        long, features, FAQ answers
  data/quality_tool_extras.json
                        same rich fields, after the build_rich merge

Hard-fail patterns: raw URLs, HTTP method names, version strings (v1.0.0,
com.x/y), snake_case function/tool names, test-log/handshake lines
("POST initialize", "returned HTTP 200", tools/list), JSON-ish text, and the
two catalog templates ("is an open-source agent project that helps builders
handle…" and "is an MCP server that gives agents a way to handle…").

Handshake and probe evidence belongs in tool_rich.json "mcp" (the tool-page
MCP server section), not in the fields above.

Diff-aware: only listings added or whose checked fields changed versus the
base commit (BASE_SHA, or origin/main) are scanned.

Run from a repo checkout:
  python3 scripts/lint_listing_copy.py
  python3 scripts/lint_listing_copy.py --base origin/main --head HEAD
Guardrails CI calls failures() from scripts/guardrails/pr_check.py.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_DEFAULT = Path(__file__).resolve().parents[1]

# Architecture / platform tokens that look like snake_case but are not tool names.
SNAKE_ALLOW = frozenset({
    "x86_64", "i686", "i386", "amd64", "aarch64", "arm64", "ppc64", "ppc64le",
    "riscv64", "mips64",
})

RE_SCHEME_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
RE_WWW_URL = re.compile(r"\bwww\.[^\s<>\"')\]]+", re.I)
RE_BARE_DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9-]+\.)+(?:com|io|ai|dev|net|org|app|xyz|so|gg|info|shop|cloud|co)"
    r"(?:/[^\s<>\"')\],;]*)?",
    re.I,
)
RE_HTTP_METHOD = re.compile(
    r"\b(?:a\s+)?(?:POST|GET|PUT|PATCH|DELETE|OPTIONS|HEAD)\b"
)
RE_VERSION = re.compile(
    r"""
    \bv\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.]+)?\b
    | \bcom\.[A-Za-z0-9_.]+/[A-Za-z0-9_.-]+
    | \bversion\s+v?\d+\.\d+\.\d+\b
    """,
    re.I | re.X,
)
RE_SNAKE = re.compile(r"\b[a-z][a-z0-9]*(_[a-z0-9]+)+\b")
RE_LOG_LINE = re.compile(
    r"""
    (?:
        (?:POST|GET|PUT|PATCH)\s+initialize
        | a\s+POST\s+initialize
        | initialize\s+(?:on|returned|as)
        | answered\s+initialize
        | returned\s+(?:com\.|HTTP\s+\d{3}|serverInfo)
        | \btools/list\b
        | \bserverInfo\b
    )
    """,
    re.I | re.X,
)
RE_INITIALIZE = re.compile(r"\binitialize\b", re.I)
RE_RETURNED_LOG = re.compile(
    r"\breturned\b.{0,80}\b(?:HTTP\s+\d{3}|com\.[A-Za-z]|serverInfo|v\d+\.\d+)|"
    r"\b(?:HTTP\s+\d{3}|com\.[A-Za-z]|serverInfo|v\d+\.\d+).{0,80}\breturned\b",
    re.I | re.S,
)
RE_JSON_ISH = re.compile(
    r"""
    \{\s*["'][A-Za-z0-9_]+["']\s*:
    | \[\s*["'][A-Za-z0-9_]+["']
    | \btools/list\b
    """,
    re.X,
)
RE_TEMPLATE_OSS = re.compile(
    r"is an open-source agent project that helps builders handle",
    re.I,
)
RE_TEMPLATE_MCP = re.compile(
    r"is an MCP server that gives agents a way to handle",
    re.I,
)
# The distinctive cores, even if the opening formula is slightly reworded.
RE_TEMPLATE_CORE_OSS = re.compile(r"helps builders handle", re.I)
RE_TEMPLATE_CORE_MCP = re.compile(r"gives agents a way to handle", re.I)

ISSUE_LABELS = {
    "raw_url": "raw URL",
    "http_method": "HTTP method name",
    "version_string": "version string",
    "snake_case_identifier": "snake_case function or tool name",
    "log_line": "test-log or handshake line",
    "initialize": "handshake 'initialize'",
    "returned_log": "handshake 'returned …' line",
    "json_ish": "JSON-ish or tools/list text",
    "ai_template": "stock catalog template",
}


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


def _load_json(text: str | None, default: Any) -> Any:
    if not text or not text.strip():
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def merge_rich(rich: dict, extras: dict) -> dict:
    """Same merge as build_rich._merge_quality_extras."""
    out: dict = {k: (dict(v) if isinstance(v, dict) else v) for k, v in (rich or {}).items()}
    for slug, add in (extras or {}).items():
        if not isinstance(add, dict):
            continue
        base = out.get(slug)
        if not base:
            out[slug] = dict(add)
            continue
        for key, value in add.items():
            if key == "faq" and base.get("faq") and value:
                have = {q[0] for q in base["faq"] if isinstance(q, (list, tuple)) and q}
                base["faq"] = list(base["faq"]) + [q for q in value if q and q[0] not in have]
            elif key == "sources" and base.get("sources") and value:
                base["sources"] = list(dict.fromkeys(list(base["sources"]) + list(value)))
            else:
                base[key] = value
    return out


def tools_by_slug(data: Any) -> dict[str, dict]:
    if not isinstance(data, list):
        return {}
    out: dict[str, dict] = {}
    for item in data:
        if isinstance(item, dict) and item.get("slug"):
            out[str(item["slug"])] = item
    return out


def _join(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str) and item.strip():
                parts.append(item.strip())
        return "\n\n".join(parts)
    return str(value).strip()


def field_map(tool: dict | None, rich: dict | None) -> dict[str, str]:
    """Watched customer-facing fields for one listing."""
    tool = tool or {}
    rich = rich if isinstance(rich, dict) else {}
    fields = {
        "description": (tool.get("description") or "").strip(),
        "pricing_detail": (tool.get("pricing_detail") or "").strip(),
        "long": _join(rich.get("long")),
        "features": _join(rich.get("features")),
    }
    answers = []
    for item in rich.get("faq") or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], str):
            answers.append(item[1].strip())
        elif isinstance(item, dict) and item.get("a"):
            answers.append(str(item["a"]).strip())
    fields["faq"] = "\n\n".join(a for a in answers if a)
    return fields


def catalog_fields(tools: dict[str, dict], rich: dict) -> dict[str, dict[str, str]]:
    slugs = set(tools) | set(rich)
    return {slug: field_map(tools.get(slug), rich.get(slug)) for slug in slugs}


def changed_fields(
    old: dict[str, dict[str, str]],
    new: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Return only added listings and fields whose text changed."""
    out: dict[str, dict[str, str]] = {}
    for slug, fields in new.items():
        prev = old.get(slug) or {}
        delta = {name: text for name, text in fields.items() if text and text != (prev.get(name) or "")}
        if delta:
            out[slug] = delta
    return out


def _already_url(hits: list[tuple[str, str]], value: str) -> bool:
    return any(typ == "raw_url" and value in excerpt for typ, excerpt in hits)


def _clip(text: str, start: int, end: int, window: int = 80) -> str:
    a = max(0, start - window)
    b = min(len(text), end + window)
    prefix = "…" if a else ""
    suffix = "…" if b < len(text) else ""
    return prefix + re.sub(r"\s+", " ", text[a:b]).strip() + suffix


def scan_text(text: str) -> list[tuple[str, str]]:
    """Return (issue_type, excerpt) hits in one field."""
    text = text or ""
    hits: list[tuple[str, str]] = []

    for match in RE_SCHEME_URL.finditer(text):
        hits.append(("raw_url", _clip(text, match.start(), match.end())))
    for match in RE_WWW_URL.finditer(text):
        if text[max(0, match.start() - 8) : match.start()].lower().endswith("://"):
            continue
        if _already_url(hits, match.group(0)):
            continue
        hits.append(("raw_url", _clip(text, match.start(), match.end())))
    for match in RE_BARE_DOMAIN.finditer(text):
        prefix = text[max(0, match.start() - 8) : match.start()].lower()
        if prefix.endswith("://") or prefix.endswith("www."):
            continue
        if _already_url(hits, match.group(0)):
            continue
        hits.append(("raw_url", _clip(text, match.start(), match.end())))

    for match in RE_HTTP_METHOD.finditer(text):
        hits.append(("http_method", _clip(text, match.start(), match.end())))

    for match in RE_VERSION.finditer(text):
        hits.append(("version_string", _clip(text, match.start(), match.end())))

    for match in RE_SNAKE.finditer(text):
        if match.group(0) in SNAKE_ALLOW:
            continue
        hits.append(("snake_case_identifier", _clip(text, match.start(), match.end())))

    if RE_LOG_LINE.search(text):
        match = RE_LOG_LINE.search(text)
        assert match is not None
        hits.append(("log_line", _clip(text, match.start(), match.end(), 110)))

    for match in RE_INITIALIZE.finditer(text):
        hits.append(("initialize", _clip(text, match.start(), match.end())))

    for match in RE_RETURNED_LOG.finditer(text):
        hits.append(("returned_log", _clip(text, match.start(), match.end())))

    for match in RE_JSON_ISH.finditer(text):
        hits.append(("json_ish", _clip(text, match.start(), match.end())))

    if (
        RE_TEMPLATE_OSS.search(text)
        or RE_TEMPLATE_MCP.search(text)
        or RE_TEMPLATE_CORE_OSS.search(text)
        or RE_TEMPLATE_CORE_MCP.search(text)
    ):
        match = (
            RE_TEMPLATE_OSS.search(text)
            or RE_TEMPLATE_MCP.search(text)
            or RE_TEMPLATE_CORE_OSS.search(text)
            or RE_TEMPLATE_CORE_MCP.search(text)
        )
        assert match is not None
        hits.append(("ai_template", _clip(text, match.start(), match.end(), 100)))

    return hits


def unique_types(hits: list[tuple[str, str]]) -> list[str]:
    seen: list[str] = []
    for typ, _excerpt in hits:
        if typ not in seen:
            seen.append(typ)
    return seen


def load_catalog(repo: Path, sha: str | None) -> dict[str, dict[str, str]]:
    tools = tools_by_slug(_load_json(_blob(repo, sha, "tools.json"), []))
    rich = _load_json(_blob(repo, sha, "tool_rich.json"), {})
    extras = _load_json(_blob(repo, sha, "data/quality_tool_extras.json"), {})
    if not isinstance(rich, dict):
        rich = {}
    if not isinstance(extras, dict):
        extras = {}
    return catalog_fields(tools, merge_rich(rich, extras))


def format_failure(slug: str, field: str, hits: list[tuple[str, str]]) -> str:
    types = unique_types(hits)
    labels = ", ".join(ISSUE_LABELS.get(typ, typ) for typ in types)
    excerpt = next((item[1] for item in hits), "")
    return (
        f"Listing copy for '{slug}' field '{field}' is written in a bot-like voice "
        f"({labels}). Customer-facing description, pricing_detail, long, features, "
        f"and FAQ answers must read like natural human writing. Put handshake and "
        f"probe evidence in tool_rich.json 'mcp', not in this field. Excerpt: {excerpt}"
    )


def failures(repo: Path, base: str, head: str) -> list[str]:
    """Lint listing fields added or changed between base and head."""
    old = load_catalog(repo, base)
    new = load_catalog(repo, head)
    messages: list[str] = []
    for slug, fields in sorted(changed_fields(old, new).items()):
        for field, text in fields.items():
            hits = scan_text(text)
            if hits:
                messages.append(format_failure(slug, field, hits))
    return messages


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
    messages = failures(repo, base, head)
    if messages:
        print("Listing copy lint failed.\n")
        for number, message in enumerate(messages, 1):
            print(f"{number}. {message}\n")
        return 1
    print("Listing copy lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
