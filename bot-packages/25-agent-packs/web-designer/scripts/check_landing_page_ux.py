#!/usr/bin/env python3
"""Check a landing-page HTML file for {{YOUR_COMPANY}} conversion and mobile basics.

Looks for one h1, a visible next step, viewport settings, wide fixed widths,
and WCAG-ish contrast when two hex colors are declared inline.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = """<!doctype html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.hero{background:#102018;color:#f4f7f2}
.bad{background:#777777;color:#888888;width:980px}
</style>
</head><body>
<h1>Book a same-day visit</h1>
<p class="hero">A written time, not a callback.</p>
<a href="/book">Hold a slot</a>
<img src="van.jpg" alt="">
<div class="bad">Overflow risk</div>
</body></html>
"""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="HTML file")
    p.add_argument("--output", help="JSON report path")
    return p


def channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def contrast(a: str, b: str) -> float:
    def lum(h: str) -> float:
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)


def analyze(html: str) -> dict:
    issues = []
    h1 = len(re.findall(r"<h1\b", html, flags=re.I))
    if h1 != 1:
        issues.append(f"{h1} h1 tags")
    if not re.search(r'name=["\']viewport["\']', html, flags=re.I):
        issues.append("viewport meta missing")
    if not re.search(r"<a\b[^>]*(book|buy|start|contact|slot|demo)", html, flags=re.I):
        issues.append("no obvious primary action link")
    wide = [int(n) for n in re.findall(r"width\s*:\s*(\d+)px", html) if int(n) > 360]
    if wide:
        issues.append(f"fixed widths above 360px: {wide}")
    missing_alt = len(re.findall(r"<img\b(?![^>]*\balt=)[^>]*>", html, flags=re.I))
    empty_alt = len(re.findall(r'<img\b[^>]*alt=["\']\s*["\']', html, flags=re.I))
    if missing_alt or empty_alt:
        issues.append(f"images missing useful alt: {missing_alt + empty_alt}")
    pairs = []
    for block in re.findall(r"\{[^{}]+\}", html):
        bg = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})", block)
        fg = re.search(r"(?<!background-)color\s*:\s*(#[0-9a-fA-F]{6})", block)
        if bg and fg:
            ratio = contrast(bg.group(1), fg.group(1))
            pairs.append({"background": bg.group(1), "ink": fg.group(1), "ratio": ratio, "aa": ratio >= 4.5})
            if ratio < 4.5:
                issues.append(f"contrast {ratio} for {fg.group(1)} on {bg.group(1)}")
    return {
        "company": "{{YOUR_COMPANY}}",
        "issues": issues,
        "contrast_pairs": pairs,
        "wireframe": [
            "Hero: one promise, one proof, one button, no second navigation story.",
            "Proof: two short quotes or one number with a source.",
            "Offer: what is included, what is not, the price or the next step.",
            "FAQ: the three objections already in the sales notes.",
            "Check 360px and 390px with zero sideways scroll before launch.",
        ],
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    html = SAMPLE if dry else Path(args.input).read_text(encoding="utf-8")
    report = analyze(html)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
