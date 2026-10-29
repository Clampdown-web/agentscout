#!/usr/bin/env python3
"""Build a brand-card spec and SVG social card for {{YOUR_COMPANY}}.

Enforces a small color and type token set, checks WCAG contrast, and emits
layout specs for the common ad, post, story, and thumbnail ratios.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SIZES = [
    {"name": "feed-portrait", "width": 1080, "height": 1350, "use": "Instagram and Facebook feed"},
    {"name": "story-reel", "width": 1080, "height": 1920, "use": "Stories, Reels, Shorts, TikTok"},
    {"name": "landscape-ad", "width": 1200, "height": 628, "use": "Link ads and OG share cards"},
    {"name": "thumbnail", "width": 1280, "height": 720, "use": "YouTube and video thumbnails"},
]

SAMPLE = {
    "brand": "{{YOUR_COMPANY}}",
    "headline": "Ship the offer, not the clutter",
    "subhead": "One clear promise. One next step.",
    "colors": {"background": "#102018", "ink": "#F4F7F2", "accent": "#7CFF6B"},
    "fonts": {"display": "Fraunces", "text": "Source Sans 3"},
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Brand kit JSON")
    p.add_argument("--output", help="Write JSON spec here")
    p.add_argument("--svg", help="Write the 1200x628 SVG here")
    return p


def channel(value: int) -> float:
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)


def svg(kit: dict) -> str:
    c = kit["colors"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="628" viewBox="0 0 1200 628">
  <rect width="1200" height="628" fill="{c["background"]}"/>
  <rect x="64" y="64" width="18" height="500" fill="{c["accent"]}"/>
  <text x="112" y="250" fill="{c["ink"]}" font-family="{kit["fonts"]["display"]}, Georgia, serif" font-size="68">{kit["headline"]}</text>
  <text x="112" y="330" fill="{c["ink"]}" font-family="{kit["fonts"]["text"]}, sans-serif" font-size="32" opacity="0.88">{kit["subhead"]}</text>
  <text x="112" y="520" fill="{c["accent"]}" font-family="{kit["fonts"]["text"]}, sans-serif" font-size="24">{kit["brand"]}</text>
</svg>
'''


def analyze(kit: dict) -> dict:
    colors = kit["colors"]
    pairs = {
        "ink_on_background": contrast(colors["ink"], colors["background"]),
        "accent_on_background": contrast(colors["accent"], colors["background"]),
    }
    failing = [name for name, ratio in pairs.items() if ratio < 4.5]
    return {
        "company": "{{YOUR_COMPANY}}",
        "brand": kit["brand"],
        "tokens": {"colors": colors, "fonts": kit["fonts"]},
        "contrast": pairs,
        "wcag_aa_text": not failing,
        "failing_pairs": failing,
        "sizes": SIZES,
        "layout_rules": [
            "Keep the headline under 8 words and inside the left two-thirds.",
            "Put the brand name in the accent color, never as a second headline.",
            "Leave at least 64px of quiet edge on every ratio before export.",
            "Do not stretch the logo. Recenter the same token set per ratio.",
        ],
        "svg_1200x628": svg(kit),
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    kit = SAMPLE if dry else json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze(kit)
    report["dry_run"] = dry
    if args.svg:
        Path(args.svg).write_text(report["svg_1200x628"], encoding="utf-8")
    text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
