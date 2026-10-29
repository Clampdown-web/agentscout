#!/usr/bin/env python3
"""Score a B2B prospect CSV against {{YOUR_COMPANY}}'s ICP rubric.

Uses firmographics and buying signals you already have. It does not call
paid enrichment vendors. Apollo, Explorium, or LeadMagic can be used by a
person later to fill empty columns; this script only scores the file.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SAMPLE = [
    {"company": "Northwind Clinic", "domain": "northwind.example", "employees": "40", "industry": "healthcare", "title": "Owner", "signal": "hiring receptionist", "email": "a@northwind.example"},
    {"company": "Northwind Clinic", "domain": "northwind.example", "employees": "40", "industry": "healthcare", "title": "Owner", "signal": "hiring receptionist", "email": "a@northwind.example"},
    {"company": "Piedmont Logistics", "domain": "piedmont.example", "employees": "800", "industry": "logistics", "title": "Intern", "signal": "", "email": "bad-email"},
    {"company": "Lumen Dental", "domain": "lumendental.example", "employees": "12", "industry": "dental", "title": "Founder", "signal": "new location", "email": "hello@lumendental.example"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Prospect CSV")
    p.add_argument("--output", help="Qualified CSV path")
    p.add_argument("--json", dest="json_out", help="Full JSON report path")
    p.add_argument("--min-score", type=int, default=60)
    return p


def email_ok(value: str) -> bool:
    if value.count("@") != 1:
        return False
    local, _, host = value.partition("@")
    return bool(local) and "." in host and " " not in value


def score_row(row: dict) -> dict:
    points = []
    employees = int(row.get("employees") or 0)
    if 5 <= employees <= 200:
        points.append(("employee_band", 25, "Inside the default small-business band"))
    elif employees > 200:
        points.append(("employee_band", 8, "Larger than the default ICP; keep only with a strong signal"))
    else:
        points.append(("employee_band", 5, "Very small team"))
    title = (row.get("title") or "").lower()
    if any(w in title for w in ("owner", "founder", "ceo", "partner", "director", "head")):
        points.append(("buyer_title", 25, "Title can approve a purchase"))
    else:
        points.append(("buyer_title", 6, "Title is not an obvious buyer"))
    signal = (row.get("signal") or "").strip()
    if signal:
        points.append(("buying_signal", 30, signal))
    else:
        points.append(("buying_signal", 0, "No signal recorded"))
    if email_ok(row.get("email") or ""):
        points.append(("email", 20, "Email shape looks usable"))
    else:
        points.append(("email", 0, "Email missing or malformed"))
    total = sum(p[1] for p in points)
    band = "qualified" if total >= 60 else "nurture" if total >= 40 else "discard"
    return {
        "company": row.get("company", ""),
        "domain": (row.get("domain") or "").lower().strip(),
        "score": total,
        "band": band,
        "reasons": [{"factor": a, "points": b, "note": c} for a, b, c in points],
    }


def analyze(rows: list[dict], min_score: int) -> dict:
    seen = set()
    scored = []
    dupes = 0
    for row in rows:
        domain = (row.get("domain") or row.get("company") or "").lower().strip()
        if domain in seen:
            dupes += 1
            continue
        seen.add(domain)
        scored.append(score_row(row))
    scored.sort(key=lambda r: r["score"], reverse=True)
    qualified = [r for r in scored if r["score"] >= min_score]
    return {
        "company": "{{YOUR_COMPANY}}",
        "icp": "Owner-led organizations with about 5-200 people and a visible buying signal.",
        "anti_icp": ["Students", "agencies reselling without a budget owner", "personal free-mail addresses with no company"],
        "duplicates_removed": dupes,
        "qualified": qualified,
        "all": scored,
        "note": "Do not email anyone until {{YOUR_OWNER_NAME}} approves the list.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    if dry:
        rows = SAMPLE
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    report = analyze(rows, args.min_score)
    report["dry_run"] = dry
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["company", "domain", "score", "band"])
            writer.writeheader()
            for row in report["qualified"]:
                writer.writerow({k: row[k] for k in writer.fieldnames})
    text = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
