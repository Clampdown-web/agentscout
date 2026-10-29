#!/usr/bin/env python3
"""Reconcile a mixed bank, invoice, and receipt ledger for {{YOUR_COMPANY}}.

Matches bank lines to invoices and receipts inside a date window and amount
tolerance, suggests a chart-of-accounts category, and lists a needs-review
queue. Stdlib only. This is bookkeeping support, not tax or legal advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

SAMPLE = [
    {"date": "2026-03-01", "description": "Stripe payout INV-1042", "amount": "1200.00", "source": "bank"},
    {"date": "2026-03-01", "description": "Invoice 1042 Northwind", "amount": "1200.00", "source": "invoice"},
    {"date": "2026-03-02", "description": "Adobe Creative Cloud", "amount": "-59.99", "source": "bank"},
    {"date": "2026-03-02", "description": "Receipt Adobe CC", "amount": "59.99", "source": "receipt"},
    {"date": "2026-03-04", "description": "Team lunch", "amount": "-84.20", "source": "bank"},
    {"date": "2026-03-18", "description": "Unmatched contractor", "amount": "-400.00", "source": "bank"},
]

KEYWORDS = [
    ("software", ("adobe", "figma", "slack", "notion", "github", "hosting")),
    ("meals", ("lunch", "dinner", "coffee", "restaurant", "uber eats")),
    ("revenue", ("stripe", "invoice", "payout", "client")),
    ("contractors", ("contractor", "freelance", "1099")),
    ("rent", ("rent", "lease", "wework")),
    ("travel", ("airfare", "hotel", "uber", "lyft", "mileage")),
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="Use the built-in sample ledger")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true", help="Same as --dry-run")
    p.add_argument("--input", help="CSV with date, description, amount, source")
    p.add_argument("--output", help="Write the JSON report here")
    p.add_argument("--days", type=int, default=3, help="Date window for a match")
    p.add_argument("--tolerance", type=float, default=0.05, help="Absolute amount tolerance")
    return p


def load_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def money(value: str) -> float:
    return round(float(str(value).replace(",", "").replace("$", "")), 2)


def day(value: str) -> datetime:
    return datetime.strptime(value[:10], "%Y-%m-%d")


def category(text: str) -> tuple[str, str]:
    low = text.lower()
    for name, words in KEYWORDS:
        if any(w in low for w in words):
            return name, "keyword"
    return "uncategorized", "needs-review"


def analyze(rows: list[dict], days: int, tolerance: float) -> dict:
    bank, docs = [], []
    for row in rows:
        item = {
            "date": row["date"][:10],
            "description": row["description"].strip(),
            "amount": abs(money(row["amount"])),
            "signed": money(row["amount"]),
            "source": row["source"].strip().lower(),
        }
        (bank if item["source"] == "bank" else docs).append(item)
    used = set()
    matched = []
    for i, line in enumerate(bank):
        hit = None
        for j, doc in enumerate(docs):
            if j in used:
                continue
            if abs(line["amount"] - doc["amount"]) > tolerance:
                continue
            if abs((day(line["date"]) - day(doc["date"])).days) > days:
                continue
            hit = j
            break
        cat, how = category(line["description"])
        if hit is None:
            continue
        used.add(hit)
        matched.append({
            "bank": line["description"],
            "document": docs[hit]["description"],
            "amount": line["amount"],
            "category": cat,
            "category_method": how,
            "status": "matched",
        })
    unmatched_bank = []
    for i, line in enumerate(bank):
        if any(m["bank"] == line["description"] for m in matched):
            continue
        cat, how = category(line["description"])
        unmatched_bank.append({
            "description": line["description"],
            "amount": line["signed"],
            "category": cat,
            "category_method": how,
            "status": "needs-review",
        })
    unmatched_docs = [d["description"] for j, d in enumerate(docs) if j not in used]
    review = [r for r in unmatched_bank if r["category"] == "uncategorized"]
    return {
        "company": "{{YOUR_COMPANY}}",
        "matched": matched,
        "unmatched_bank": unmatched_bank,
        "unmatched_documents": unmatched_docs,
        "needs_review": review,
        "close_checklist": [
            "Confirm every unmatched bank line with a receipt or invoice.",
            "Post accruals and prepaid expenses before the month locks.",
            "Flag contractor payments that may need a 1099 conversation with a tax professional.",
            "This report is not a filed tax return.",
        ],
        "counts": {
            "matched": len(matched),
            "unmatched_bank": len(unmatched_bank),
            "unmatched_documents": len(unmatched_docs),
        },
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or getattr(args, 'self_test', False) or not args.input
    rows = SAMPLE if dry else load_rows(args.input)
    report = analyze(rows, args.days, args.tolerance)
    report["dry_run"] = dry
    text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
