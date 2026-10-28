#!/usr/bin/env python3
"""Build an accounts-receivable aging report for {{YOUR_COMPANY}}.

Buckets open invoices and suggests a tone step. Late fees appear only when
the contract flag is set. It does not email anyone.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

SAMPLE = [
    {"invoice": "1042", "customer": "Northwind", "amount": "1200", "due": "2026-03-01", "paid": "0", "contract_late_fee": "yes"},
    {"invoice": "1048", "customer": "Lumen", "amount": "480", "due": "2026-04-01", "paid": "480", "contract_late_fee": "no"},
    {"invoice": "1051", "customer": "Piedmont", "amount": "900", "due": "2026-01-15", "paid": "0", "contract_late_fee": "no"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Invoice CSV")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--as-of", default="2026-04-06")
    p.add_argument("--late-fee-pct", type=float, default=1.5, help="Monthly percent, only if the contract allows it")
    return p


def bucket(days: int) -> str:
    if days <= 0:
        return "current"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def tone(days: int) -> str:
    if days <= 0:
        return "upcoming reminder three days before due"
    if days <= 7:
        return "polite note with the payment link"
    if days <= 30:
        return "firm reminder, still warm"
    if days <= 60:
        return "second firm notice and a phone task"
    return "owner escalation, pause if there is a written dispute"


def analyze(rows: list[dict], as_of: date, fee_pct: float) -> dict:
    open_rows = []
    totals = {"current": 0.0, "1-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    for row in rows:
        amount = float(row["amount"])
        paid = float(row.get("paid") or 0)
        due_amt = round(amount - paid, 2)
        if due_amt <= 0:
            continue
        due = datetime.strptime(row["due"][:10], "%Y-%m-%d").date()
        days = (as_of - due).days
        name = bucket(days)
        totals[name] += due_amt
        fee = 0.0
        if days > 0 and str(row.get("contract_late_fee", "")).lower() in {"yes", "true", "1"}:
            fee = round(due_amt * (fee_pct / 100) * max(1, days / 30), 2)
        open_rows.append({
            "invoice": row["invoice"],
            "customer": row["customer"],
            "open_amount": due_amt,
            "days_past_due": days,
            "bucket": name,
            "tone": tone(days),
            "late_fee_if_contract_allows": fee,
            "payment_link": "https://{{YOUR_DOMAIN}}/pay/" + row["invoice"],
        })
    receivable = round(sum(totals.values()), 2)
    return {
        "company": "{{YOUR_COMPANY}}",
        "as_of": as_of.isoformat(),
        "buckets": {k: round(v, 2) for k, v in totals.items()},
        "open_receivable": receivable,
        "invoices": open_rows,
        "rules": [
            "Put the payment link in every note.",
            "If the customer disputes the invoice in writing, pause the ladder.",
            "Do not invent a late fee the contract does not allow.",
            "{{YOUR_OWNER_NAME}} approves anything past 30 days.",
        ],
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    if dry:
        rows = SAMPLE
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    report = analyze(rows, date.fromisoformat(args.as_of), args.late_fee_pct)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
