#!/usr/bin/env python3
"""Diff two competitor snapshots for {{YOUR_COMPANY}}.

Compares price and feature keys. Every claim should already carry a source
URL and an as-of date. The script does not browse the web by itself.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAMPLE = {
    "ours": {
        "name": "{{YOUR_COMPANY}}",
        "as_of": "2026-04-01",
        "source_url": "https://{{YOUR_DOMAIN}}/pricing",
        "price_monthly": 49,
        "features": ["same-day slot", "written quote", "sms reminder"],
    },
    "theirs": {
        "name": "Example Rival",
        "as_of": "2026-04-01",
        "source_url": "https://example.com/pricing",
        "price_monthly": 79,
        "features": ["same-day slot", "call center", "annual contract"],
    },
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="JSON with ours and theirs objects")
    p.add_argument("--output", help="JSON report path")
    return p


def analyze(doc: dict) -> dict:
    ours, theirs = doc["ours"], doc["theirs"]
    issues = []
    for side, obj in (("ours", ours), ("theirs", theirs)):
        if not obj.get("source_url") or not obj.get("as_of"):
            issues.append(f"{side} is missing source_url or as_of")
    our_f, their_f = set(ours.get("features", [])), set(theirs.get("features", []))
    price_delta = None
    if "price_monthly" in ours and "price_monthly" in theirs:
        price_delta = round(float(ours["price_monthly"]) - float(theirs["price_monthly"]), 2)
    return {
        "company": "{{YOUR_COMPANY}}",
        "issues": issues,
        "only_ours": sorted(our_f - their_f),
        "only_theirs": sorted(their_f - our_f),
        "shared": sorted(our_f & their_f),
        "monthly_price_delta_ours_minus_theirs": price_delta,
        "positioning": [
            "Lead with a feature only we have, and name the source date.",
            "If they are cheaper, say who the cheaper plan is for instead of hiding the number.",
            "Do not quote a review you cannot link.",
        ],
        "launch_watch": "Re-run when either pricing URL changes, not on a rumor.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    doc = SAMPLE if dry else json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = analyze(doc)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
