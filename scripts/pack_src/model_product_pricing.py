#!/usr/bin/env python3
"""Model a three-tier price and a small MVP cut for {{YOUR_COMPANY}}.

Uses cost, target margin, and a simple reach/impact/confidence/effort score.
It does not change a live price.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAMPLE = {
    "cost_per_customer_month": 9,
    "target_gross_margin": 0.75,
    "annual_discount": 0.15,
    "features": [
        {"name": "Written slot", "reach": 5, "impact": 5, "confidence": 0.8, "effort": 2, "mvp": True},
        {"name": "SMS reminder", "reach": 4, "impact": 4, "confidence": 0.7, "effort": 3, "mvp": True},
        {"name": "Multi-location payroll", "reach": 2, "impact": 3, "confidence": 0.4, "effort": 8, "mvp": False},
    ],
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Pricing JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def rice(item: dict) -> float:
    effort = max(0.5, float(item.get("effort") or 1))
    return round(float(item["reach"]) * float(item["impact"]) * float(item["confidence"]) / effort, 2)


def analyze(doc: dict) -> dict:
    margin = float(doc["target_gross_margin"])
    cost = float(doc["cost_per_customer_month"])
    if margin >= 1:
        raise SystemExit("target_gross_margin must be below 1")
    good = round(cost / (1 - margin), 2)
    better = round(good * 1.8, 2)
    best = round(good * 3.2, 2)
    annual = float(doc.get("annual_discount") or 0)
    features = []
    for item in doc.get("features", []):
        features.append({**item, "rice": rice(item)})
    features.sort(key=lambda r: r["rice"], reverse=True)
    mvp = [f["name"] for f in features if f.get("mvp")]
    later = [f["name"] for f in features if not f.get("mvp")]
    return {
        "company": "{{YOUR_COMPANY}}",
        "tiers": {
            "good": {"monthly": good, "annual_monthly": round(good * (1 - annual), 2), "includes": mvp[:1] or ["core workflow"]},
            "better": {"monthly": better, "annual_monthly": round(better * (1 - annual), 2), "includes": mvp},
            "best": {"monthly": best, "annual_monthly": round(best * (1 - annual), 2), "includes": mvp + ["priority setup with {{YOUR_OWNER_NAME}}"]},
        },
        "mvp_keep": mvp,
        "cut_from_mvp": later,
        "ranked_features": features,
        "launch_checks": [
            "One sentence problem statement a buyer repeats back.",
            "Success metric with a baseline and a date.",
            "Non-goals written down so the sprint cannot absorb them.",
            "Support path {{YOUR_SUPPORT_EMAIL}} is live before the first charge.",
        ],
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
