#!/usr/bin/env python3
"""Lint a cold-email sequence for {{YOUR_COMPANY}} before anyone sends it.

Checks length, a single ask, spam-trigger words, spacing, and the bulk-sender
basics (unsubscribe line and a physical-address placeholder). DNS is reported
as a checklist, not a live lookup, unless --domain is passed to a local note.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = {
    "mailbox": "hello@{{YOUR_DOMAIN}}",
    "steps": [
        {"day": 0, "subject": "Question about Northwind's second location", "body": "Alex, saw the new location posting. We help clinics book the first visit the same afternoon. Worth a 12-minute look next week?\n\n{{YOUR_OWNER_NAME}}\n{{YOUR_COMPANY}}\n123 Market Street\nUnsubscribe: reply stop"},
        {"day": 1, "subject": "FREE GUARANTEED leads!!!", "body": "Act now. Click here. Buy now. Winner. " * 40},
        {"day": 5, "subject": "Closing the loop", "body": "Should I close the file, or is a short walkthrough useful?\n\nUnsubscribe: reply stop\n123 Market Street"},
    ],
}

SPAM = ("free", "guarantee", "guaranteed", "act now", "winner", "click here", "buy now", "risk-free", "100%", "limited time", "no obligation")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Sequence JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text)


def analyze(doc: dict) -> dict:
    findings = []
    previous = None
    for i, step in enumerate(doc["steps"], start=1):
        body = step["body"]
        count = len(words(body))
        low = body.lower()
        asks = len(re.findall(r"\?", body))
        hits = [w for w in SPAM if w in low]
        issues = []
        if count > 125:
            issues.append(f"{count} words; keep the email under 125")
        if asks != 1:
            issues.append(f"{asks} questions; use one ask")
        if hits:
            issues.append("spam-trigger words: " + ", ".join(hits))
        if "unsubscribe" not in low and "reply stop" not in low:
            issues.append("missing a human unsubscribe line")
        if not re.search(r"\d+\s+\w+\s+(street|st|ave|road|rd|blvd)", low):
            issues.append("missing a physical mailing address line")
        if previous is not None and step["day"] - previous < 2:
            issues.append("step is closer than 2 days; give the thread room")
        previous = step["day"]
        findings.append({"step": i, "day": step["day"], "subject": step["subject"], "words": count, "issues": issues})
    return {
        "company": "{{YOUR_COMPANY}}",
        "mailbox": doc.get("mailbox", ""),
        "steps": findings,
        "ready_to_draft": all(not row["issues"] for row in findings),
        "deliverability_checklist": [
            "SPF includes the sending vendor and ends in one all mechanism.",
            "DKIM signs the visible From domain.",
            "DMARC is at least p=none while you watch reports, then tighter.",
            "Keep complaint rate under 0.3% and honor unsubscribe within 10 business days (CAN-SPAM).",
            "One-click list-unsubscribe for bulk mail to Google and Yahoo recipients.",
        ],
        "approval": "Do not send until {{YOUR_OWNER_NAME}} approves each mailbox batch.",
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
