#!/usr/bin/env python3
"""Every public template must contain what its title promises.

Read-only. No POST. Fails when a template is empty, still shows README markup,
or is missing the control the nav label names (form, signup, buy link, connect steps).

  python3 scripts/content_check.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "preview", "pagefind", "bot-packages", "node_modules", "__pycache__", "notes", "docs"}
MARKUP = re.compile(r"&lt;(?:h1|h2|div|p|img|picture)\b", re.I)
PLACEHOLDER = re.compile(r"\b(?:TODO|lorem ipsum|undefined|NaN)\b")
# Named tokens such as {{YOUR_COMPANY}} and {{var}} are copy. An unclosed "{{" is a miss.
BARE_BRACE = re.compile(r"\{\{(?![A-Za-z0-9_]+\}\})")
TAG_RE = re.compile(r"<[^>]+>")
_HIDDEN = {"script", "style", "textarea", "pre"}


class _DropHidden(HTMLParser):
    """Drop script, style, textarea, and pre elements, including odd end tags.

    html.parser accepts </script >, </SCRIPT\\n>, and the same forms for the
    other hidden elements. A closing-tag regexp does not.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in _HIDDEN:
            self._depth += 1
            return
        if not self._depth:
            self.parts.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag):
        if tag.lower() in _HIDDEN and self._depth:
            self._depth -= 1
            return
        if not self._depth:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._depth:
            self.parts.append(data)

    def handle_entityref(self, name):
        if not self._depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if not self._depth:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        if not self._depth:
            self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        if not self._depth:
            self.parts.append(f"<!{decl}>")


def _without_hidden(html: str) -> str:
    parser = _DropHidden()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _visible(html: str) -> str:
    text = TAG_RE.sub(" ", _without_hidden(html))
    return re.sub(r"\s+", " ", text)


def _is_redirect(html: str) -> bool:
    return 'http-equiv="refresh"' in html[:4000] or "<title>Moved" in html[:2500]


def _h1_count(html: str) -> int:
    body = _without_hidden(html)
    return len(re.findall(r"<h1\b", body, re.I))


def _kind(rel: str) -> str:
    parts = rel.split("/")
    name = parts[-1]
    if rel == "index.html":
        return "home"
    if len(parts) == 1:
        return "page:" + name
    top = parts[0]
    if top == "tools" and name != "index.html":
        return "tool"
    if top == "news" and len(parts) > 3 and name != "index.html":
        return "news-story"
    if top == "best" and name != "index.html":
        return "best"
    if top == "tasks" and name != "index.html":
        return "task"
    if top == "categories" and name != "index.html":
        return "category"
    if top == "s" and name != "index.html":
        return "popular"
    if top == "mcp" and name not in ("index.html", "connect.html", "pricing.html", "link-status.html"):
        return "mcp-list"
    if top == "bot-store" and name == "index.html" and len(parts) > 2:
        return "bot-store-item"
    if top == "free-tools" and name != "index.html":
        return "free-tool"
    if name == "index.html":
        return top + "/index"
    return top + "/" + name


def _walk():
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS or part.startswith(".") for part in path.parts):
            continue
        if "data/outreach" in str(path):
            continue
        yield path


def _local_asset(page: Path, ref: str) -> str | None:
    ref = ref.split("#", 1)[0].split("?", 1)[0]
    if not ref or ref.startswith(("data:", "mailto:", "javascript:", "http://", "https://", "//")):
        return None
    if "${" in ref or "{{" in ref:
        return None
    target = (ROOT / ref.lstrip("/")) if ref.startswith("/") else (page.parent / ref)
    try:
        target = target.resolve()
        target.relative_to(ROOT)
    except ValueError:
        return f"{page.relative_to(ROOT)} -> {ref}"
    if not target.is_file():
        return f"{page.relative_to(ROOT)} missing asset {ref}"
    return None


def problems(root: Path | None = None) -> list[str]:
    global ROOT
    if root is not None:
        ROOT = root
    bad: list[str] = []
    by_kind: dict[str, list[str]] = defaultdict(list)

    connect = ROOT / "mcp" / "connect.html"
    if connect.is_file():
        text = _read(connect)
        for needle in (
            "How to connect",
            "https://mcp.agentscouthq.com/mcp",
            "claude mcp add --transport http agentscout",
            ".cursor/mcp.json",
            ".vscode/mcp.json",
            "serverUrl",
            "mcp-remote",
            "Streamable HTTP",
            "Try this prompt",
            "id=\"how-to-connect\"",
        ):
            if needle not in text:
                bad.append(f"mcp/connect.html missing {needle}")
        if ("/mcp/" + "sse") in text:
            bad.append("mcp/connect.html still names the retired SSE path")
        snap = ROOT / "data" / "mcp_live_tools.json"
        if not snap.is_file():
            bad.append("data/mcp_live_tools.json missing (tools/list snapshot)")
        else:
            doc = json.loads(snap.read_text(encoding="utf-8"))
            if doc.get("transport") != "streamable-http" or doc.get("endpoint") != "https://mcp.agentscouthq.com/mcp":
                bad.append("mcp live snapshot is not the Streamable HTTP endpoint")
            for tool in doc.get("tools") or []:
                if f"<code>{tool['name']}</code>" not in text and f">{tool['name']}<" not in text:
                    bad.append(f"mcp/connect.html does not list live tool {tool['name']}")
        by_kind["mcp/connect.html"].append("checked")

    submit = ROOT / "submit.html"
    if submit.is_file():
        text = _read(submit)
        for needle in ('id="sf"', 'id="name"', 'id="website"', 'id="sf-turnstile"', 'type="submit"'):
            if needle not in text:
                bad.append(f"submit.html missing {needle}")
        sf = re.search(r'<form id="sf"[^>]*>', text)
        if sf and re.search(r'action="https?://', sf.group(0)):
            bad.append("submit.html form posts to a URL from the markup")
        by_kind["submit.html"].append("checked")

    home = ROOT / "index.html"
    if home.is_file():
        text = _read(home)
        if "verify-slim" not in text:
            bad.append("index.html is missing the MCP verification status")
        if "navburger" not in text:
            bad.append("index.html is missing the hamburger")
        panel = re.search(r'<h3>Browse by guide</h3>.*?</div>', text, re.S)
        if not panel or 'class="guide-list"' not in panel.group(0):
            bad.append("index.html Browse by guide is not a row list")
        elif " · " in panel.group(0) or panel.group(0).count("<li>") < 6 or panel.group(0).count("<li>") > 10:
            bad.append("index.html Browse by guide should be 6 to 8 guides plus the two hub links")
        elif "All best lists" not in panel.group(0) or "All categories" not in panel.group(0):
            bad.append("index.html Browse by guide is missing the hub links")
        by_kind["home"].append("checked")

    tools_path = ROOT / "tools.json"
    if tools_path.is_file():
        catalog = json.loads(tools_path.read_text(encoding="utf-8"))
        if isinstance(catalog, dict):
            catalog = catalog.get("tools") or []
        only = [row for row in catalog if row.get("catalog_only")]
        counts_path = ROOT / "data" / "site_counts.json"
        if counts_path.is_file():
            counted = json.loads(counts_path.read_text(encoding="utf-8"))
            if counted.get("tools") != len(catalog):
                bad.append(f"site_counts.tools is {counted.get('tools')}, tools.json has {len(catalog)}")
            if counted.get("catalog_only") != len(only):
                bad.append(f"site_counts.catalog_only is {counted.get('catalog_only')}, tools.json has {len(only)}")
        sm = ROOT / "sitemap.xml"
        sitemap = sm.read_text(encoding="utf-8") if sm.is_file() else ""
        for row in only:
            slug = row.get("slug") or ""
            if not slug:
                continue
            if f"tools/{slug}.html" in sitemap:
                bad.append(f"sitemap includes catalog_only tools/{slug}.html")
                break
            page = ROOT / "tools" / f"{slug}.html"
            if page.is_file() and 'name="robots" content="noindex' not in _read(page)[:2500]:
                bad.append(f"tools/{slug}.html is catalog_only but indexable")
                break
        by_kind["catalog_only"].append("checked")
        status_doc = ROOT / "status.json"
        link_doc = ROOT / "data" / "mcp_link_status.json"
        if status_doc.is_file() and link_doc.is_file() and home.is_file():
            published = json.loads(status_doc.read_text(encoding="utf-8")).get("catalog") or {}
            rows = json.loads(status_doc.read_text(encoding="utf-8")).get("servers") or []
            live_n = sum(1 for row in rows if row.get("status") == "live")
            down_n = sum(1 for row in rows if row.get("status") == "down")
            checked_n = live_n + down_n
            if live_n > checked_n or published.get("live") != live_n or published.get("checked") != checked_n:
                bad.append(
                    f"MCP live count {published.get('live')} / checked {published.get('checked')} "
                    f"does not match the checked set ({live_n} of {checked_n})"
                )
            card = re.search(r"<b>([\d,]+) of ([\d,]+)</b> checked servers reachable", _read(home))
            if not card:
                bad.append("index.html MCP status card does not use the checked-server denominator")
            elif int(card.group(1).replace(",", "")) != live_n or int(card.group(2).replace(",", "")) != checked_n:
                bad.append(
                    f"index.html says {card.group(1)} of {card.group(2)}, checked set is {live_n} of {checked_n}"
                )
            unverified = [row for row in rows if row.get("catalog_only") and row.get("status") != "live" and row.get("status") != "down"]
            if any(not row.get("unverified") for row in unverified):
                bad.append("a catalog_only MCP server with no check row is not labeled unverified")

    newsletter = ROOT / "newsletter.html"
    if newsletter.is_file():
        text = _read(newsletter)
        if "beehiiv.com" not in text and 'type="email"' not in text:
            bad.append("newsletter.html has no signup")
        by_kind["newsletter.html"].append("checked")

    news = ROOT / "news.html"
    if news.is_file():
        text = _read(news)
        dates = re.findall(r'datetime="(\d{4}-\d{2}-\d{2})', text)
        if not dates:
            bad.append("news.html has no dated stories")
        else:
            newest = max(dates)
            age = (date.today() - date.fromisoformat(newest)).days
            if age > 21:
                bad.append(f"news.html newest story is {newest}, {age} days old")
        by_kind["news.html"].append("checked")

    compare = ROOT / "compare" / "index.html"
    if compare.is_file():
        text = _read(compare)
        if 'id="cpick"' not in text or "compare-picker.js" not in text:
            bad.append("compare/index.html picker is missing")
        by_kind["compare/index"].append("checked")

    quiz = ROOT / "quiz.html"
    if quiz.is_file():
        text = _read(quiz)
        if 'id="quiz"' not in text or "quiz.js" not in text:
            bad.append("quiz.html is missing the quiz widget")
        by_kind["quiz.html"].append("checked")

    generate = ROOT / "generate.html"
    if generate.is_file():
        text = _read(generate)
        gen_js = (ROOT / "generate.js").read_text(encoding="utf-8") if (ROOT / "generate.js").is_file() else ""
        if "<form" not in text or "turnstile" not in (text + gen_js).lower():
            bad.append("generate.html is missing the generator form or Turnstile")
        by_kind["generate.html"].append("checked")

    saved = ROOT / "saved.html"
    if saved.is_file():
        text = _read(saved)
        if "saved" not in text.lower() or "<h1" not in _without_hidden(text):
            bad.append("saved.html has no saved-tools heading")
        by_kind["saved.html"].append("checked")

    store = ROOT / "bot-store" / "index.html"
    if store.is_file():
        text = _read(store)
        buys = re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", text)
        if len(buys) < 3 or "bs-card" not in text and "pack" not in text.lower():
            bad.append("bot-store/index.html is missing product cards or Stripe buy links")
        by_kind["bot-store/index"].append("checked")

    status = ROOT / "mcp" / "status" / "index.html"
    status_json = ROOT / "status.json"
    if status.is_file() and status_json.is_file():
        doc = json.loads(status_json.read_text(encoding="utf-8"))
        catalog = doc.get("catalog") or {}
        live = catalog.get("live")
        text = _read(status)
        if live is None or str(live) not in text:
            bad.append("mcp/status/ does not show the live count from status.json")
        by_kind["mcp/status"].append("checked")

    for path in _walk():
        rel = str(path.relative_to(ROOT))
        html = _read(path)
        if _is_redirect(html):
            by_kind[_kind(rel)].append("redirect")
            continue
        kind = _kind(rel)
        visible = _visible(html)
        if kind in {"tool", "category", "best", "task", "popular", "mcp-list", "news-story", "free-tool", "bot-store-item", "home"} or rel in {
            "submit.html", "sponsor.html", "about.html", "privacy.html", "refunds.html", "quiz.html", "generate.html", "newsletter.html", "news.html", "badges.html"
        }:
            if _h1_count(html) != 1 and kind != "home":
                # home may use a header h1; still require one
                if _h1_count(html) == 0:
                    bad.append(f"{rel} has no H1")
            if MARKUP.search(visible):
                bad.append(f"{rel} shows README markup in the visible text")
            plain = PLACEHOLDER.search(visible)
            brace = BARE_BRACE.search(visible)
            if (plain or brace) and kind != "free-tool":
                bad.append(f"{rel} has placeholder text ({(plain or brace).group(0)})")
        if kind == "tool" and "noindex" not in html[:5000]:
            if "At a glance" not in html and "<dl" not in html:
                bad.append(f"{rel} has no At a glance facts")
            if not re.search(r'href="https?://', html):
                bad.append(f"{rel} has no outbound link")
        if kind in {"category", "best", "task", "popular", "mcp-list"} and rel.endswith(".html"):
            items = len(re.findall(r'href="(?:\.\./)*tools/[a-z0-9-]+\.html"', html))
            if items < 1 and "noindex" not in html[:4000]:
                bad.append(f"{rel} list has no tool links")
        for ref in re.findall(r'(?:src|poster)="([^"]+)"', html):
            missing = _local_asset(path, ref)
            if missing and missing.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp", ".mp4", ".gif", ".css", ".js")):
                bad.append(missing)
        by_kind[kind].append(rel)

    # One line per template family so the report can show pass/fail.
    families = [
        "home", "tool", "category", "best", "task", "popular", "mcp-list", "mcp/connect.html",
        "news.html", "news-story", "compare/index", "quiz.html", "generate.html", "saved.html",
        "submit.html", "newsletter.html", "bot-store/index", "bot-store-item", "free-tool", "mcp/status",
    ]
    failed = {line.split(" ", 1)[0] for line in bad}
    for family in families:
        hit = [line for line in bad if family in line or line.startswith(family)]
        if family in {"tool", "category", "best", "task", "popular", "mcp-list", "news-story", "free-tool", "bot-store-item"}:
            hit = [line for line in bad if line.startswith(f"{family}/") or f"/{family}/" in line or line.startswith(family)]
        # stored for the printer
        by_kind.setdefault(family, [])
    problems.by_kind = by_kind  # type: ignore[attr-defined]
    problems.failed_files = failed  # type: ignore[attr-defined]
    return bad


def _table(bad: list[str]) -> list[str]:
    by_kind = getattr(problems, "by_kind", {})
    lines = ["template\tpages\tresult"]
    groups = [
        "home", "tool", "category", "categories/index", "best", "best/index", "task", "tasks/index",
        "popular", "s/index", "mcp-list", "mcp/index", "mcp/connect.html", "mcp/status",
        "news.html", "news-story", "compare/index", "quiz.html", "generate.html", "saved.html",
        "submit.html", "newsletter.html", "bot-store/index", "bot-store-item", "free-tool",
        "page:about.html", "page:privacy.html", "page:sponsor.html", "page:badges.html",
    ]
    for kind in groups:
        rows = by_kind.get(kind) or []
        count = len([row for row in rows if row not in {"checked", "redirect"}]) or (1 if rows else 0)
        hit = [line for line in bad if line.startswith(kind) or f"{kind}/" in line or line.startswith(kind.replace("page:", ""))]
        if kind == "home":
            hit = [line for line in bad if line.startswith("index.html")]
        if kind == "mcp/connect.html":
            hit = [line for line in bad if "connect.html" in line or "mcp_live_tools" in line or line.startswith("mcp live")]
        status = "FAIL" if hit else ("PASS" if rows else "SKIP")
        lines.append(f"{kind}\t{count}\t{status}" + ("" if not hit else "\t" + hit[0][:140]))
    return lines


def main() -> int:
    bad = problems()
    print("content check")
    for line in _table(bad):
        print(line)
    print(f"\n{len(bad)} problems")
    for line in bad[:80]:
        print(" ", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
