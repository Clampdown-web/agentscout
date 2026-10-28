#!/usr/bin/env python3
"""Apply kill-or-scale rules to an ad CSV for {{YOUR_COMPANY}}.

Computes ROAS, CPA, CTR, and a fatigue flag. Spend changes stay as
recommendations until a person approves them.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SAMPLE = [
    {"campaign": "Angle A", "spend": "400", "revenue": "1600", "impressions": "20000", "clicks": "500", "conversions": "40", "frequency": "1.4", "ctr_last_week": "0.031"},
    {"campaign": "Angle B", "spend": "350", "revenue": "180", "impressions": "18000", "clicks": "120", "conversions": "4", "frequency": "4.2", "ctr_last_week": "0.018"},
    {"campaign": "Angle C", "spend": "40", "revenue": "0", "impressions": "2000", "clicks": "30", "conversions": "0", "frequency": "1.1", "ctr_last_week": "0.02"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Ads CSV")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--target-roas", type=float, default=2.0)
    p.add_argument("--max-cpa", type=float, default=40)
    p.add_argument("--min-spend", type=float, default=150)
    return p


def f(row: dict, key: str) -> float:
    return float(row.get(key) or 0)


def analyze(rows: list[dict], target: float, max_cpa: float, min_spend: float) -> dict:
    out = []
    for row in rows:
        spend, revenue = f(row, "spend"), f(row, "revenue")
        clicks, impressions = f(row, "clicks"), f(row, "impressions")
        conversions = f(row, "conversions")
        roas = round(revenue / spend, 2) if spend else 0
        cpa = round(spend / conversions, 2) if conversions else None
        ctr = round(clicks / impressions, 4) if impressions else 0
        last = f(row, "ctr_last_week")
        fatigue = f(row, "frequency") >= 3.5 and last and ctr < last * 0.75
        if spend < min_spend:
            action = "hold"
            why = "Spend is under the learning floor. Do not judge it yet."
        elif fatigue:
            action = "refresh-creative"
            why = "Frequency is high and CTR faded versus last week."
        elif roas >= target and (cpa is None or cpa <= max_cpa) and conversions >= 15:
            action = "scale"
            why = "ROAS and CPA clear the bar with enough conversions to trust."
        elif roas < target or (cpa is not None and cpa > max_cpa):
            action = "kill-or-rebuild"
            why = "Efficiency missed the written rule after the spend floor."
        else:
            action = "hold"
            why = "Mixed signal. Wait for more conversions."
        out.append({
            "campaign": row["campaign"],
            "roas": roas,
            "cpa": cpa,
            "ctr": ctr,
            "frequency": f(row, "frequency"),
            "fatigue": fatigue,
            "action": action,
            "why": why,
        })
    return {
        "company": "{{YOUR_COMPANY}}",
        "rules": {"target_roas": target, "max_cpa": max_cpa, "min_spend": min_spend},
        "campaigns": out,
        "creative_matrix": "Test three hooks, three bodies, and three calls to action, changing one cell at a time.",
        "utm_check": "Every ad URL needs utm_source, utm_medium, utm_campaign, and utm_content before spend moves.",
        "approval": "Do not change budget until {{YOUR_OWNER_NAME}} accepts the action column.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    if dry:
        rows = SAMPLE
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    report = analyze(rows, args.target_roas, args.max_cpa, args.min_spend)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
