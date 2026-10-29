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
    if not LOVABLE.is_file():
        bad.append("tools/lovable.html missing")
        _report(bad)
        return 1
    html = LOVABLE.read_text(encoding="utf-8")
    section_count = html.count(f'id="{SECTION_ID}"')
    if section_count != 1:
        bad.append(f"tools/lovable.html has {section_count} 25 AI Agent Packs sections, expected 1")
    h2 = len(re.findall(r"<h2[^>]*>\s*25 AI Agent Packs\s*</h2>", html))
    if h2 != 1:
        bad.append(f"tools/lovable.html has {h2} '25 AI Agent Packs' headings, expected 1")
    if "25 AI Agent Packs" not in html:
        bad.append("tools/lovable.html lacks the 25 AI Agent Packs section")
    m = re.search(
        rf'<!--lovable-agent-packs-->.*?<!--/lovable-agent-packs-->',
        html,
        re.S,
    )
    block = m.group(0) if m else ""
    if not block:
        bad.append("tools/lovable.html lacks the marked 25 AI Agent Packs section")
    else:
        for price in PRICES:
            if price not in block:
                bad.append(f"25 AI Agent Packs section missing {price}")
        for url in STRIPE:
            n = block.count(url)
            if n != 1:
                bad.append(f"25 AI Agent Packs section has {n} copies of {url}, expected 1")
    if "application/ld+json" not in html or "SoftwareApplication" not in html:
        bad.append("tools/lovable.html missing SoftwareApplication JSON-LD")
    nav = re.search(r"<nav\b[^>]*>.*?</nav>", html, re.S)
    foot = re.search(r"<footer\b[^>]*>.*?</footer>", html, re.S)
    if not nav:
        bad.append("tools/lovable.html missing sitewide nav")
    elif "npill" not in nav.group(0):
        bad.append("tools/lovable.html nav missing neon pills")
    if not foot:
        bad.append("tools/lovable.html missing sitewide footer")
    elif "bot-store/" not in foot.group(0):
        bad.append("tools/lovable.html footer missing Bot Store")
    if STORE.is_file():
        store = STORE.read_text(encoding="utf-8")
        for url in STRIPE:
            if url not in store:
                bad.append(f"bot-store/index.html missing Stripe Payment Link {url}")
        if 'id="ai-agent-packs"' not in store:
            bad.append("bot-store/index.html missing #ai-agent-packs")
    else:
        bad.append("bot-store/index.html missing")
    bad.extend(_follower_row_problems())
    bad.extend(_pack_page_problems())
    _report(bad)
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


def _pack_page_problems() -> list[str]:
    """Every role pack page shows its verification date and Product + HowTo JSON-LD."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from agent_pack_catalog import AGENTS
    from start_here import GUIDE_LINE, SETUP_LINE, tested_line, verified_on, works_with_for_zip

    problems = []
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
    for rel in ("bot-store/index.html", "bot-templates/index.html"):
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"{rel} missing")
            continue
        text = path.read_text(encoding="utf-8")
        shown = text.count("Tested on ")
        if shown < 25:
            problems.append(f"{rel} shows {shown} Tested on lines, expected 25")
        if text.count(GUIDE_LINE) < 25:
            problems.append(f"{rel} is missing the START HERE mention on a pack card")
        if text.count(SETUP_LINE) < 25:
            problems.append(f"{rel} is missing the 10-minute line on a pack card")
    return problems


def _report(bad: list[str]) -> None:
    print(f"daily_deep_audit: {len(bad)} problems")
    for line in bad:
        print("FAIL", line)
    if not bad:
        print("PASS tools/lovable.html has exactly one 25 AI Agent Packs section")
        print("PASS nav, footer, neon pills, JSON-LD, and Stripe Payment Links ($35/$119/$199/$299/$349)")
        print("PASS follower rows are fetched for their own day when the sprint tracker is present")


if __name__ == "__main__":
    sys.exit(main())
