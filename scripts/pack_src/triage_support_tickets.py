#!/usr/bin/env python3
"""Triage support tickets for {{YOUR_COMPANY}} into intent, priority, and route.

Drafts a macro outline. It does not refund, close, or email the customer.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SAMPLE = [
    {"id": "T-100", "subject": "Need a refund for order 88", "body": "The visit never happened. Please refund today.", "created": "2026-04-04T15:00:00Z"},
    {"id": "T-101", "subject": "How do I reschedule", "body": "Can I move Thursday to Friday?", "created": "2026-04-04T15:10:00Z"},
    {"id": "T-102", "subject": "Injury on site", "body": "Someone was hurt. This is a legal issue.", "created": "2026-04-04T15:12:00Z"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Ticket CSV")
    p.add_argument("--output", help="JSON report path")
    return p


def classify(row: dict) -> dict:
    text = f"{row.get('subject','')} {row.get('body','')}".lower()
    if any(w in text for w in ("lawyer", "legal", "injury", "hurt", "unsafe", "police")):
        intent, priority, route = "safety-or-legal", "p0", "owner"
    elif any(w in text for w in ("refund", "chargeback", "charged twice", "cancel")):
        intent, priority, route = "refund", "p1", "billing-macro"
    elif any(w in text for w in ("bug", "error", "broken", "down", "outage")):
        intent, priority, route = "incident", "p1", "specialist"
    elif any(w in text for w in ("how", "reschedule", "where", "password", "hours")):
        intent, priority, route = "how-to", "p3", "knowledge-base"
    else:
        intent, priority, route = "general", "p2", "inbox"
    sla = {"p0": "15 minutes", "p1": "4 hours", "p2": "1 business day", "p3": "2 business days"}[priority]
    return {
        "id": row.get("id", ""),
        "intent": intent,
        "priority": priority,
        "sla": sla,
        "route": route,
        "macro": f"Acknowledge the request, cite the matching policy section, and tell them the next update window ({sla}).",
        "escalate": route == "owner",
    }


def analyze(rows: list[dict]) -> dict:
    items = [classify(row) for row in rows]
    return {
        "company": "{{YOUR_COMPANY}}",
        "support_email": "{{YOUR_SUPPORT_EMAIL}}",
        "tickets": items,
        "p0": [t["id"] for t in items if t["priority"] == "p0"],
        "refund_rule": "Refunds follow the written policy in context/business-profile.md. Do not invent an exception.",
        "approval": "Send nothing until a person confirms the macro.",
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
