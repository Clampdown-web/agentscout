#!/usr/bin/env python3
"""Audit a local HTML file or the buyer's own URL for {{YOUR_COMPANY}}.

Checks title, description, headings, canonical, JSON-LD, image alts, and a
sibling llms.txt note. Optional --url uses the standard library to fetch one
page the operator names. It does not crawl a directory and it does not invent
Core Web Vitals lab numbers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

SAMPLE_HTML = """<!doctype html><html><head>
<title>{{YOUR_COMPANY}} books visits the same day</title>
<meta name="description" content="Same-day visits from {{YOUR_COMPANY}} for owners who want a written time, not a callback.">
<link rel="canonical" href="https://{{YOUR_DOMAIN}}/">
<script type="application/ld+json">{"@type":"Organization","name":"{{YOUR_COMPANY}}"}</script>
</head><body>
<h1>Book a visit today</h1>
<img src="hero.jpg" alt="Technician at a front door">
<a href="/pricing">Pricing</a>
</body></html>
"""


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = []
        self.in_title = False
        self.metas = []
        self.h1 = 0
        self.canonical = ""
        self.jsonld = 0
        self.imgs = []
        self.links = 0
        self._img = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.jsonld += 1
        elif tag == "img":
            self.imgs.append(a.get("alt"))
        elif tag == "a":
            self.links += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Local HTML file")
    p.add_argument("--url", help="Fetch this single URL with urllib")
    p.add_argument("--output", help="JSON report path")
    return p


def meta_desc(page: Page) -> str:
    for meta in page.metas:
        if meta.get("name", "").lower() == "description":
            return meta.get("content", "")
    return ""


def analyze(html: str, source: str) -> dict:
    page = Page()
    page.feed(html)
    title = " ".join(page.title).strip()
    desc = meta_desc(page)
    missing_alt = sum(1 for alt in page.imgs if not alt)
    issues = []
    if not (15 <= len(title) <= 65):
        issues.append(f"title length is {len(title)}; aim for 15-65 characters")
    if not (50 <= len(desc) <= 160):
        issues.append(f"meta description length is {len(desc)}; aim for 50-160")
    if page.h1 != 1:
        issues.append(f"found {page.h1} h1 elements; use one")
    if not page.canonical:
        issues.append("canonical link missing")
    if page.jsonld == 0:
        issues.append("no JSON-LD block")
    if missing_alt:
        issues.append(f"{missing_alt} images without alt text")
    return {
        "company": "{{YOUR_COMPANY}}",
        "source": source,
        "title": title,
        "meta_description": desc,
        "h1_count": page.h1,
        "canonical": page.canonical,
        "json_ld_blocks": page.jsonld,
        "internal_links_seen": page.links,
        "images_missing_alt": missing_alt,
        "llms_txt": "Place a llms.txt next to the site root and list the canonical pages a model may quote.",
        "core_web_vitals": "Not measured here. Use field data from Search Console before you claim LCP, INP, or CLS.",
        "issues": issues,
        "aeo_notes": [
            "Answer one buyer question in the first screen.",
            "Cite a primary source when you state a number.",
            "Keep the visible name consistent with the Organization JSON-LD name.",
        ],
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not (args.input or args.url)
    if dry:
        html, source = SAMPLE_HTML, "sample"
    elif args.url:
        req = Request(args.url, headers={"User-Agent": "{{YOUR_COMPANY}} seo-audit"})
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "replace")
        source = args.url
    else:
        html, source = Path(args.input).read_text(encoding="utf-8"), args.input
    report = analyze(html, source)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
