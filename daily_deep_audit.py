#!/usr/bin/env python3
"""Local site audit for the built HTML.

Fails when tools/lovable.html is missing the 25 AI Agent Packs section,
when that section is duplicated, or when the page lost its nav, footer,
neon pills, JSON-LD, or the $35/$119/$199/$299/$349 Stripe Payment Links.
Also checks the Bot Store still carries those same Payment Links.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOVABLE = ROOT / "tools" / "lovable.html"
STORE = ROOT / "bot-store" / "index.html"
SECTION_ID = "lovable-agent-packs"
STRIPE = (
    "https://buy.stripe.com/00w6oI0uDaBF8gZ5jle7m09",
    "https://buy.stripe.com/9B600kfpx4dhbtb8vxe7m0a",
    "https://buy.stripe.com/6oU8wQ4KT4dh0OxeTVe7m0b",
    "https://buy.stripe.com/5kQ28s1yH5hl8gZ8vxe7m0c",
    "https://buy.stripe.com/28E9AUdhpfVZ0OxbHJe7m0d",
)
PRICES = ("$35", "$119", "$199", "$299", "$349")


def main() -> int:
    bad: list[str] = []
    follower = _follower_row_problems()
    bad.extend(follower)
    pack_bad, pack_pass = _pack_page_problems()
    bad.extend(pack_bad)
    chrome = _chrome_checks()
    ops = _ops_checks()
    named = chrome + ops
    bad.extend(label for ok, label in named if not ok)
    passes = [label for ok, label in named if ok] + pack_pass
    import build_seo_new
    pill = build_seo_new.header_pill_problems()
    bad.extend(pill)
    if not pill:
        passes.append("header nav has one free-tools.html link and no duplicate nav pills")
    if not follower:
        passes.append("follower rows are fetched for their own day when the sprint tracker is present")
    scroll = _scroll_button_problems()
    bad.extend(scroll)
    if not scroll:
        passes.append("portrait scroll buttons stay available at max-width 640px")
    _report(bad, passes)
    return 1 if bad else 0


def _follower_row_problems() -> list[str]:
    """Fail a sprint-tracker row that was copied forward instead of fetched that day."""
    path = ROOT / "data" / "30-day-sprint-tracker.json"
    if not path.is_file():
        print("sprint tracker: not present, follower-row check skipped")
        return []
    sys.path.insert(0, str(ROOT / "scripts"))
    import sync_x_followers

    try:
        tracker = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"data/30-day-sprint-tracker.json is not valid JSON ({exc})"]
    return [f"sprint tracker: {line}" for line in sync_x_followers.audit_tracker(tracker)]


def _walk_types(node, found: list) -> None:
    if isinstance(node, dict):
        kind = node.get("@type")
        if isinstance(kind, str):
            found.append((kind, node))
        elif isinstance(kind, list):
            for item in kind:
                if isinstance(item, str):
                    found.append((item, node))
        for value in node.values():
            _walk_types(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_types(item, found)


def _chrome_checks() -> list[tuple[bool, str]]:
    """One result per Lovable section fact and per Bot Store Payment Link."""
    checks: list[tuple[bool, str]] = []
    if not LOVABLE.is_file():
        checks.append((False, "tools/lovable.html missing"))
        return checks
    page = LOVABLE.read_text(encoding="utf-8")
    section_count = page.count(f'id="{SECTION_ID}"')
    checks.append((section_count == 1, f"tools/lovable.html has {section_count} 25 AI Agent Packs sections, expected 1" if section_count != 1 else "tools/lovable.html has exactly one 25 AI Agent Packs section"))
    h2 = len(re.findall(r"<h2[^>]*>\s*25 AI Agent Packs\s*</h2>", page))
    checks.append((h2 == 1, f"tools/lovable.html has {h2} '25 AI Agent Packs' headings, expected 1" if h2 != 1 else "tools/lovable.html has one 25 AI Agent Packs heading"))
    checks.append(("25 AI Agent Packs" in page, "tools/lovable.html includes the 25 AI Agent Packs section"))
    marked = re.search(r"<!--lovable-agent-packs-->.*?<!--/lovable-agent-packs-->", page, re.S)
    block = marked.group(0) if marked else ""
    checks.append((bool(block), "tools/lovable.html has the marked 25 AI Agent Packs section"))
    for price in PRICES:
        checks.append((bool(block) and price in block, f"25 AI Agent Packs section includes {price}"))
    for url in STRIPE:
        count = block.count(url) if block else 0
        checks.append((count == 1, f"25 AI Agent Packs section includes {url} once"))
    checks.append(("application/ld+json" in page, "tools/lovable.html has JSON-LD"))
    checks.append(("SoftwareApplication" in page, "tools/lovable.html has SoftwareApplication JSON-LD"))
    nav = re.search(r"<nav\b[^>]*>.*?</nav>", page, re.S)
    checks.append((bool(nav), "tools/lovable.html has the sitewide nav"))
    checks.append((bool(nav) and "npill" in nav.group(0), "tools/lovable.html nav has neon pills"))
    foot = re.search(r"<footer\b[^>]*>.*?</footer>", page, re.S)
    checks.append((bool(foot), "tools/lovable.html has the sitewide footer"))
    checks.append((bool(foot) and "bot-store/" in foot.group(0), "tools/lovable.html footer links to the Bot Store"))
    if not STORE.is_file():
        checks.append((False, "bot-store/index.html missing"))
        return checks
    store = STORE.read_text(encoding="utf-8")
    for url in STRIPE:
        checks.append((url in store, f"bot-store/index.html includes Stripe Payment Link {url}"))
    checks.append(('id="ai-agent-packs"' in store, "bot-store/index.html has #ai-agent-packs"))
    return checks


def _ops_checks() -> list[tuple[bool, str]]:
    """Homepage cache-buster, template total, and the submit category contract."""
    import build_seo_new
    from build_bot_templates import template_count_agreement

    checks: list[tuple[bool, str]] = []
    token = "?v=" + build_seo_new.animation_cache_buster()
    index_path = ROOT / "index.html"
    if not index_path.is_file():
        checks.append((False, f"4b homepage animation cache-buster {token} is missing from index.html"))
    else:
        index = index_path.read_text(encoding="utf-8")
        anims = re.findall(r'(?:src|poster)="(assets/animations/[^"]+)"', index)
        stale = [url for url in anims if not url.endswith(token)]
        if not anims or stale:
            checks.append((False, f"4b homepage animation cache-buster {token} is missing from index.html"))
        else:
            checks.append((True, f"4b homepage animation cache-buster {token}"))
    parts = template_count_agreement()
    label = (
        f"bot templates {parts['total']} "
        f"(built-in {parts['builtin']} + community {parts['community']})"
    )
    if parts["missing"] or parts["page"] != parts["total"] or parts["total"] < 1:
        missing = ", ".join(parts["missing"][:5])
        checks.append((False, f"{label} but the page has {parts['page']} rows" + (f" missing {missing}" if missing else "")))
    else:
        checks.append((True, label))
    submit = ROOT / "submit.html"
    select = ""
    if submit.is_file():
        match = re.search(r'<select id="category"[^>]*>.*?</select>', submit.read_text(encoding="utf-8"), re.S)
        select = match.group(0) if match else ""
    options = re.findall(r'<option\b([^>]*)>(.*?)</option>', select, re.S) if select else []
    values = []
    for attrs, text in options:
        value = ""
        found = re.search(r'value="([^"]*)"', attrs)
        if found:
            value = html.unescape(found.group(1)).strip()
        if not value:
            value = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
        values.append(value)
    if not select or not values or any(not value for value in values):
        checks.append((False, 'submit.html is missing <select id="category"> option values'))
    else:
        checks.append((True, f'submit.html <select id="category"> has {len(values)} option values'))
    catalog = ROOT / "categories.json"
    try:
        published = json.loads(catalog.read_text(encoding="utf-8")) if catalog.is_file() else None
    except json.JSONDecodeError:
        published = None
    if published != values or not values:
        checks.append((False, "categories.json does not match the submit category option values"))
    else:
        checks.append((True, f"categories.json lists {len(values)} submit categories"))
    return checks


def _pack_page_problems() -> tuple[list[str], list[str]]:
    """Every role pack page shows its verification date and Product + HowTo JSON-LD."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from agent_pack_catalog import AGENTS
    from start_here import GUIDE_LINE, SETUP_LINE, tested_line, verified_on, works_with_for_zip

    problems = []
    passes: list[str] = []
    zip_root = ROOT / "bot-packages" / "25-agent-packs" / "zips"
    for agent in AGENTS:
        rel = f"bot-store/{agent['slug']}/index.html"
        page = ROOT / "bot-store" / agent["slug"] / "index.html"
        if not page.is_file():
            problems.append(f"{rel} missing")
            continue
        page_html = page.read_text(encoding="utf-8")
        tested = tested_line(agent["slug"])
        if not tested:
            problems.append(f"{rel} has no successful verification, so it cannot show Tested on")
        elif tested not in page_html:
            problems.append(f"{rel} missing {tested}")
        works = works_with_for_zip(zip_root / f"{agent['slug']}.zip")
        if not works:
            problems.append(f"{rel} ZIP does not support a Works with line")
        elif works not in page_html:
            problems.append(f"{rel} missing {works}")
        if GUIDE_LINE not in page_html:
            problems.append(f"{rel} missing {GUIDE_LINE}")
        meta = re.search(r'<meta name="description" content="([^"]*)"', page_html)
        if not meta or not html.unescape(meta.group(1)).startswith(SETUP_LINE):
            problems.append(f"{rel} description does not start with the 10-minute line")
        if f'class="pack-setupline">{SETUP_LINE}' not in page_html:
            problems.append(f"{rel} visible description does not start with the 10-minute line")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page_html, re.S)
        typed: list[tuple[str, dict]] = []
        for block in blocks:
            try:
                data = json.loads(block)
            except json.JSONDecodeError as exc:
                problems.append(f"{rel} JSON-LD is not valid JSON ({exc})")
                continue
            _walk_types(data, typed)
        products = [node for kind, node in typed if kind == "Product"]
        howtos = [node for kind, node in typed if kind == "HowTo"]
        day = verified_on(agent["slug"])
        if len(products) != 1:
            problems.append(f"{rel} has {len(products)} Product JSON-LD nodes")
        else:
            if products[0].get("dateModified") != day:
                problems.append(f"{rel} Product dateModified is {products[0].get('dateModified')!r}, verification date is {day!r}")
            offer = products[0].get("offers") or {}
            if isinstance(offer, dict) and "priceValidUntil" in offer and offer.get("priceValidUntil") != day:
                problems.append(f"{rel} Offer priceValidUntil is {offer.get('priceValidUntil')!r}")
        if len(howtos) != 1:
            problems.append(f"{rel} has {len(howtos)} HowTo JSON-LD nodes")
        else:
            steps = howtos[0].get("step") or []
            if not isinstance(steps, list) or len(steps) < 4:
                problems.append(f"{rel} HowTo has {0 if not isinstance(steps, list) else len(steps)} steps")
            else:
                names = [step.get("name") for step in steps if isinstance(step, dict)]
                for required in ("Import the template", "Connect tools", "Run the first task"):
                    if required not in names:
                        problems.append(f"{rel} HowTo missing step {required}")
                for step in steps:
                    if not isinstance(step, dict) or step.get("@type") != "HowToStep" or not step.get("text"):
                        problems.append(f"{rel} HowTo step is missing @type HowToStep or text")
                        break
        if not any(item.startswith(rel) for item in problems):
            passes.append(f"{rel} Tested on, Product dateModified, and HowTo")
    for rel in ("bot-store/index.html", "bot-templates/index.html"):
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"{rel} missing")
            continue
        text = path.read_text(encoding="utf-8")
        before = len(problems)
        shown = text.count("Tested on ")
        if shown < 25:
            problems.append(f"{rel} shows {shown} Tested on lines, expected 25")
        if text.count(GUIDE_LINE) < 25:
            problems.append(f"{rel} is missing the START HERE mention on a pack card")
        if text.count(SETUP_LINE) < 25:
            problems.append(f"{rel} is missing the 10-minute line on a pack card")
        if len(problems) == before:
            passes.append(f"{rel} shows Tested on, START HERE, and the 10-minute line")
    return problems, passes


def _brace_span(text: str, open_at: int) -> tuple[str, int]:
    """Return the inside of the brace that starts at open_at, and the index after its close."""
    depth = 0
    i = open_at
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_at + 1:i], i + 1
        i += 1
    return text[open_at + 1:], len(text)


def _rule_hides_scrollbtns(body: str) -> bool:
    """True when this already-matched max-width:640px block hides .scrollbtns."""
    i = 0
    while i < len(body):
        brace = body.find("{", i)
        if brace < 0:
            return False
        sel = body[i:brace]
        inner, nxt = _brace_span(body, brace)
        head = sel.strip()
        if head.startswith("@media") or head.startswith("@supports"):
            if _rule_hides_scrollbtns(inner):
                return True
        elif ".scrollbtns" in sel and re.search(r"display\s*:\s*none\b", inner, re.I):
            return True
        i = nxt
    return False


def _media_hides_scrollbtns(css: str) -> bool:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i = 0
    while True:
        match = re.search(r"@media\b", css[i:])
        if not match:
            return False
        start = i + match.start()
        brace = css.find("{", start)
        if brace < 0:
            return False
        header = css[start:brace]
        body, end = _brace_span(css, brace)
        if re.search(r"max-width\s*:\s*640px", header, re.I) and _rule_hides_scrollbtns(body):
            return True
        i = end


def _scroll_button_problems() -> list[str]:
    """Fail if phone portrait hides .scrollbtns again, or the kept exceptions disappear."""
    problems: list[str] = []
    css_path = ROOT / "styles.css"
    if not css_path.is_file():
        return ["styles.css missing; cannot check portrait scroll buttons"]
    css = re.sub(r"/\*.*?\*/", "", css_path.read_text(encoding="utf-8"), flags=re.S)
    if not re.search(r"@media\s+print\s*\{[^}]*\.scrollbtns\s*\{[^}]*display\s*:\s*none\b", css):
        problems.append("styles.css print rule no longer hides .scrollbtns")
    if not re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{[^}]*\.scrollbtn\s*\{[^}]*transition\s*:\s*none\b", css):
        problems.append("styles.css lost prefers-reduced-motion on .scrollbtn")
    if not re.search(r"body:has\(\.lb-board\)\s+\.scrollbtns\s*\{[^}]*display\s*:\s*none\b", css):
        problems.append("styles.css no longer hides .scrollbtns on body:has(.lb-board)")
    literal = re.compile(
        r"@media[^{]{0,200}max-width\s*:\s*640px[^{]{0,120}\{[^}]{0,500}\.scrollbtns\s*\{[^}]{0,200}display\s*:\s*none\b",
        re.I | re.S,
    )
    skip = {".git", "node_modules", "preview", "pagefind", "assets"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in skip for part in path.parts):
            continue
        if path.suffix.lower() not in {".css", ".js", ".html"}:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if ".scrollbtns" not in text or "640" not in text:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() == ".css" and _media_hides_scrollbtns(text):
            problems.append(f"{rel} hides .scrollbtns at max-width:640px")
        elif literal.search(re.sub(r"/\*.*?\*/", "", text, flags=re.S)):
            problems.append(f"{rel} hides .scrollbtns at max-width:640px")
    js_path = ROOT / "app.js"
    if js_path.is_file():
        js = js_path.read_text(encoding="utf-8")
        block = re.search(r"/\* Scroll buttons.*?\}\)\(\);", js, re.S)
        chunk = block.group(0) if block else ""
        if not chunk or "scrollbtn up" not in chunk or "scrollbtn down" not in chunk:
            problems.append("app.js no longer creates the up/down scroll buttons")
        elif re.search(r"innerWidth\s*[<]=?\s*640|matchMedia\(\s*[\"'][^\"']*max-width\s*:\s*640px", chunk):
            problems.append("app.js skips scroll buttons at max-width 640px")
    return problems


def _report(bad: list[str], passes: list[str] | None = None) -> None:
    passes = passes or []
    total = len(bad) + len(passes)
    if bad:
        print(f"daily_deep_audit: {len(passes)}/{total} PASS")
        for line in bad:
            print("FAIL", line)
        return
    print(f"daily_deep_audit: {total}/{total} PASS")
    for line in passes:
        print("PASS", line)


if __name__ == "__main__":
    sys.exit(main())
