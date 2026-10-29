#!/usr/bin/env python3
"""Summarize a monthly KPI CSV for {{YOUR_COMPANY}}.

Computes MRR change, logo churn, a simple LTV, and flags months that sit
more than 1.5 standard deviations off the recent mean.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

SAMPLE = [
    {"month": "2026-01", "mrr": "20000", "new_mrr": "3000", "churned_mrr": "800", "customers": "100", "new_customers": "12", "churned_customers": "4"},
    {"month": "2026-02", "mrr": "22000", "new_mrr": "2800", "churned_mrr": "900", "customers": "106", "new_customers": "10", "churned_customers": "4"},
    {"month": "2026-03", "mrr": "18000", "new_mrr": "1000", "churned_mrr": "4200", "customers": "96", "new_customers": "4", "churned_customers": "14"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="KPI CSV")
    p.add_argument("--output", help="JSON report path")
    return p


def num(row: dict, key: str) -> float:
    return float(row.get(key) or 0)


def analyze(rows: list[dict]) -> dict:
    months = []
    for row in rows:
        customers = max(1.0, num(row, "customers"))
        churned = num(row, "churned_customers")
        mrr = num(row, "mrr")
        logo_churn = churned / customers
        arpu = mrr / customers
        ltv = arpu / logo_churn if logo_churn else None
        months.append({
            "month": row["month"],
            "mrr": round(mrr, 2),
            "net_new_mrr": round(num(row, "new_mrr") - num(row, "churned_mrr"), 2),
            "logo_churn_rate": round(logo_churn, 4),
            "arpu": round(arpu, 2),
            "ltv_simple": None if ltv is None else round(ltv, 2),
        })
    nets = [m["net_new_mrr"] for m in months]
    mean = statistics.fmean(nets) if nets else 0
    stdev = statistics.pstdev(nets) if len(nets) > 1 else 0
    anomalies = []
    for month in months:
        z = 0 if stdev == 0 else (month["net_new_mrr"] - mean) / stdev
        month["z"] = round(z, 2)
        if abs(z) >= 1.5:
            anomalies.append({"month": month["month"], "metric": "net_new_mrr", "z": month["z"]})
    latest = months[-1] if months else {}
    narrative = []
    if latest:
        narrative.append(f"Latest MRR is {latest['mrr']}.")
        narrative.append(f"Net new MRR is {latest['net_new_mrr']}.")
        narrative.append("Treat LTV as directional until finance signs the gross-margin assumption.")
    return {
        "company": "{{YOUR_COMPANY}}",
        "months": months,
        "anomalies": anomalies,
        "narrative": narrative,
        "chart_hint": "Plot MRR as bars and logo churn as a line. Do not dual-axis without labeling both units.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
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
