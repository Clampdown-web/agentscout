#!/usr/bin/env python3
"""Restamp pages that read data/mcp-health without a full site build.

build_site.py calls the network, rewrites tools.json, and stamps the Pacific
date. The daily handshake job only needs the fragments those builders copy out
of the health summary and the latest probe row: the badge, the Responds
data-resp attributes, the Our check block, and the handshake sentence.

The sitemap is not rewritten. A new sitemap URL or a new HTML document is a
hard failure. The daily indexable-page cap for this job is zero.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "guardrails"))

import mcp_response_rate as mrr  # noqa: E402
from pages import is_published_html, sitemap_locs  # noqa: E402

SKIP_DIRS = {
    ".git",
    ".github",
    "assets",
    "bot-packages",
    "cloudflare-api-worker",
    "cloudflare-image-worker-patches",
    "cloudflare-mcp-worker",
    "data",
    "node_modules",
    "og",
    "pagefind",
    "preview",
    "reports",
    "scripts",
}
TEXT_SUFFIXES = {".html", ".txt", ".json"}
CADENCE_FALLBACK = (
    "This is the initialize + tools/list probe, updated daily around 7:15 AM Pacific, "
    "separate from the link check around 7 AM PT."
)


def _quiet_builder_hooks() -> None:
    """Importing the builders registers exit hooks that rewrite the site."""
    import atexit

    import build_extras

    for hook in (getattr(build_extras, "_apply_featured", None), getattr(build_extras, "_pf_last", None)):
        if hook is not None:
            try:
                atexit.unregister(hook)
            except Exception:
                pass


def _quote(escaped: bool) -> str:
    # A JSON file stores the markup with a backslash before each quote.
    # The regex has to match that backslash; a plain \" is only a quote.
    return r'\\"' if escaped else '"'


def _patterns(escaped: bool) -> tuple[re.Pattern[str], re.Pattern[str], re.Pattern[str]]:
    q = _quote(escaped)
    badge = re.compile(rf'<span class={q}b{q} data-mcp-health={q}1{q}>[^<]*</span>')
    resp = re.compile(
        rf'\sdata-resp={q}[01]{q}(?:\sdata-rr={q}[0-9.]+{q})?(?:\sdata-rn={q}\d+{q})?'
    )
    slug_attr = re.compile(rf'data-s={q}([a-z0-9-]+){q}')
    return badge, resp, slug_attr


_HREF = re.compile(r"tools/([a-z0-9-]+)\.html")
_SECTION = re.compile(r'<section class="mcp-check" data-mcp-check="1".*?</section>', re.S)
_HAND_ROW = re.compile(r'<div class="vs-row vs-hand">.*?</div>', re.S)
_REVIEWS = '<section id="reviews"'


def _escaped_markup(text: str) -> bool:
    return 'data-mcp-health=\\"1\\"' in text or 'data-resp=\\"' in text


def _encode(html: str, escaped: bool) -> str:
    if not escaped:
        return html
    return html.replace('"', '\\"')


def _slug_before(text: str, start: int, slug_attr: re.Pattern[str], default_slug: str | None) -> str | None:
    window = text[max(0, start - 4000) : start]
    attrs = list(slug_attr.finditer(window))
    if attrs:
        return attrs[-1].group(1)
    hrefs = list(_HREF.finditer(window))
    if hrefs:
        return hrefs[-1].group(1)
    return default_slug


def _slug_for_resp(text: str, start: int, slug_attr: re.Pattern[str]) -> str | None:
    tag = text.rfind("<", max(0, start - 1200), start)
    prefix = text[tag:start] if tag >= 0 else ""
    found = slug_attr.search(prefix)
    if found:
        return found.group(1)
    ahead = _HREF.search(text[start : start + 900])
    if ahead:
        return ahead.group(1)
    behind = list(_HREF.finditer(text[max(0, start - 900) : start]))
    if behind:
        return behind[-1].group(1)
    return None


def rewrite_document(
    text: str,
    *,
    servers: dict,
    default_slug: str | None = None,
    sentence: str = "",
    home_html: str = "",
    check_html: str | None = None,
    cadence: str = CADENCE_FALLBACK,
) -> tuple[str, list[str]]:
    """Return the updated document and any badges or sort attributes left unresolved."""
    missed: list[str] = []
    escaped = _escaped_markup(text)
    badge_re, resp_re, slug_attr = _patterns(escaped)
    source = text

    def badge_sub(match: re.Match[str]) -> str:
        slug = _slug_before(source, match.start(), slug_attr, default_slug if not escaped else None)
        if not slug:
            missed.append("badge")
            return match.group(0)
        return _encode(mrr.badge_html_for(slug, servers), escaped)

    text = badge_re.sub(badge_sub, source)

    def resp_sub(match: re.Match[str]) -> str:
        slug = _slug_for_resp(text, match.start(), slug_attr)
        if not slug:
            missed.append("responds")
            return match.group(0)
        return _encode(mrr.responds_attrs(slug, servers), escaped)

    text = resp_re.sub(resp_sub, text)

    if sentence and cadence:
        pattern = re.compile(r"Handshake check: .*?" + re.escape(cadence), re.S)
        # A lambda keeps a "\1" in generated text from being read as a backreference.
        text = pattern.sub(lambda _match: sentence, text)

    if home_html and not escaped and _HAND_ROW.search(text):
        text = _HAND_ROW.sub(lambda _match: home_html, text, count=1)

    if not escaped and default_slug is not None and check_html is not None:
        if _SECTION.search(text):
            text = _SECTION.sub(lambda _match: check_html, text, count=1)
        elif check_html and _REVIEWS in text:
            text = text.replace(_REVIEWS, check_html + _REVIEWS, 1)
    return text, missed


def _tool_slug(path: Path, root: Path) -> str | None:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return None
    if rel.startswith("tools/") and rel.endswith(".html") and rel.count("/") == 1:
        return path.stem
    return None


def iter_documents(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".")]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.name in {"tools.json", "tool_rich.json", "package-lock.json"}:
                continue
            yield path


def new_sitemap_urls(root: Path, before: str, after: str) -> list[str]:
    """Normalized sitemap URLs present after the restamp and absent before it."""
    del root
    old = set(sitemap_locs(before or ""))
    new = sitemap_locs(after or "")
    return [new[norm] for norm in new.keys() - old]


def rebuild_pages(root: Path) -> dict:
    """Restamp health fragments under root. Raise SystemExit if a sitemap URL would be added."""
    _quiet_builder_hooks()
    import build_aicite as bac
    import build_extras

    root = root.resolve()
    build_extras._MCP_PROBES = None
    summary_path = root / "data" / "mcp-health" / "summary.json"
    servers = mrr.summary_servers(root, reload=True)
    sentence = bac.handshake_sentence(path=str(summary_path))
    home_html = bac.handshake_home_html(path=str(summary_path))
    cadence = bac.HANDSHAKE_CADENCE
    sitemap_path = root / "sitemap.xml"
    before_sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.is_file() else ""
    changed = 0
    missed: list[str] = []
    for path in iter_documents(root):
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        slug = _tool_slug(path, root)
        check = None
        if slug is not None:
            check = build_extras.mcp_check_html({"slug": slug}, root=str(root))
        updated, problems = rewrite_document(
            original,
            servers=servers,
            default_slug=slug,
            sentence=sentence,
            home_html=home_html,
            check_html=check,
            cadence=cadence,
        )
        if problems:
            missed.append(f"{path.relative_to(root).as_posix()}: {', '.join(problems)}")
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    after_sitemap = sitemap_path.read_text(encoding="utf-8") if sitemap_path.is_file() else ""
    added = new_sitemap_urls(root, before_sitemap, after_sitemap)
    if added:
        shown = ", ".join(added[:12])
        extra = len(added) - min(len(added), 12)
        if extra > 0:
            shown += f", and {extra} more"
        raise RuntimeError(
            "Health rebuild would add sitemap URLs, which this daily job must not publish "
            f"({len(added)}): {shown}"
        )
    if before_sitemap != after_sitemap:
        raise RuntimeError("Health rebuild changed sitemap.xml without a new URL. This job does not rewrite the sitemap.")
    if missed:
        preview = "; ".join(missed[:8])
        raise RuntimeError(f"Health rebuild could not match a slug for {len(missed)} fragment(s): {preview}")
    return {"files": changed, "sitemap_urls_added": 0}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Restamp pages that read data/mcp-health.")
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        report = rebuild_pages(args.repo)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"restamped {report['files']} file(s); new sitemap urls {report['sitemap_urls_added']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
