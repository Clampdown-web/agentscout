#!/usr/bin/env python3
"""Estimate creator engagement and a rough deal ROI for {{YOUR_COMPANY}}.

Flags engagement rates that are unusually high for the follower count. It
does not accuse a person of fraud; it marks the row for a human look.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SAMPLE = [
    {"creator": "Ava Lane", "followers": "20000", "avg_likes": "900", "avg_comments": "80", "audience_match": "0.7", "price": "600", "expected_orders": "18", "aov": "48"},
    {"creator": "Huge Reach", "followers": "500000", "avg_likes": "200", "avg_comments": "2", "audience_match": "0.2", "price": "4000", "expected_orders": "5", "aov": "48"},
    {"creator": "Spike", "followers": "80000", "avg_likes": "40000", "avg_comments": "9000", "audience_match": "0.5", "price": "1500", "expected_orders": "10", "aov": "48"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Creator CSV")
    p.add_argument("--output", help="JSON report path")
    return p


def f(row: dict, key: str) -> float:
    return float(row.get(key) or 0)


def analyze(rows: list[dict]) -> dict:
    out = []
    for row in rows:
        followers = max(1.0, f(row, "followers"))
        interactions = f(row, "avg_likes") + f(row, "avg_comments")
        rate = interactions / followers
        price = f(row, "price")
        revenue = f(row, "expected_orders") * f(row, "aov")
        roi = round((revenue - price) / price, 2) if price else None
        cpm = round(price / (followers / 1000), 2) if followers else None
        flag = None
        if rate > 0.2:
            flag = "engagement is far above a typical organic range; review the audience before you pay"
        elif rate < 0.005 and followers > 50000:
            flag = "very low engagement on a large account"
        fit = round(rate * 100 * f(row, "audience_match"), 2)
        out.append({
            "creator": row["creator"],
            "engagement_rate": round(rate, 4),
            "fit_score": fit,
            "cpm": cpm,
            "estimated_roi": roi,
            "review_flag": flag,
        })
    out.sort(key=lambda r: r["fit_score"], reverse=True)
    return {
        "company": "{{YOUR_COMPANY}}",
        "creators": out,
        "brief": [
            "State the one job the product does.",
            "Require an on-screen and caption disclosure.",
            "Usage rights: organic 30 days unless the contract says otherwise.",
            "Pay on delivery of the live URL, not on a promise.",
        ],
        "approval": "{{YOUR_OWNER_NAME}} sends the outreach. This file is a shortlist only.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    if dry:
        rows = SAMPLE
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    report = analyze(rows)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
