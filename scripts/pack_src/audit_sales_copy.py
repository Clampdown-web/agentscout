#!/usr/bin/env python3
"""Audit sales copy for {{YOUR_COMPANY}} using clarity, proof, and CTA checks.

Scores a rough readability index, looks for PAS or AIDA coverage, and flags
vague claims. It does not publish the page.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = """Tired of quotes that sit in the inbox for a week?
{{YOUR_COMPANY}} books the visit in one afternoon.
Owners told us they lost jobs while waiting on a callback.
Get a written slot today at https://{{YOUR_DOMAIN}}/book.
No jargon. A real time on your calendar.
"""

WEASEL = ("very", "really", "cutting-edge", "world-class", "seamless", "unlock", "elevate", "leverage", "robust")
PROOF = ("told us", "customer", "percent", "%", "review", "case", "hours", "days", "saved")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Plain-text or Markdown copy")
    p.add_argument("--output", help="JSON report path")
    return p


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def flesch(text: str) -> float:
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    sents = max(1, len(sentences(text)))
    syllables = 0
    for word in words:
        groups = re.findall(r"[aeiouy]+", word.lower())
        syllables += max(1, len(groups))
    score = 206.835 - 1.015 * (len(words) / sents) - 84.6 * (syllables / len(words))
    return round(score, 1)


def analyze(text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    words = re.findall(r"[A-Za-z']+", text)
    low = text.lower()
    long = [s for s in sentences(text) if len(s.split()) > 25]
    cta = len(re.findall(r"https?://|book|buy|start|get a|schedule|reply", low))
    framework = {
        "problem": any(w in low for w in ("tired", "problem", "lost", "stuck", "without")),
        "agitate": any(w in low for w in ("while", "cost", "waiting", "risk")),
        "solution": "{{your_company}}" in low or "we " in low,
        "action": cta > 0,
    }
    return {
        "company": "{{YOUR_COMPANY}}",
        "word_count": len(words),
        "sentence_count": len(sentences(text)),
        "readability_index": flesch(text),
        "readability_note": "Higher is easier. Aim near 60 or above for a public offer page.",
        "framework_coverage": framework,
        "framework_complete": all(framework.values()),
        "cta_signals": cta,
        "weasel_words": sorted({w for w in WEASEL if re.search(rf"\b{w}\b", low)}),
        "proof_signals": sorted({w for w in PROOF if w in low}),
        "long_sentences": long[:5],
        "headline_candidates": lines[:3],
        "recommendation": "Keep one promise, one proof line, and one next step above the fold.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    text = SAMPLE if dry else Path(args.input).read_text(encoding="utf-8")
    report = analyze(text)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
