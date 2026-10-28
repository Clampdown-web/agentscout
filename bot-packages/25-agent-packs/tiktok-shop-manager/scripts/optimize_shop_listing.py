#!/usr/bin/env python3
"""Lint a shop listing and estimate affiliate commission for {{YOUR_COMPANY}}.

Flags thin titles, risky claims, low image counts, and low stock. It does
not publish the listing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAMPLE = {
    "title": "Same-day booking kit for clinic front desks",
    "description": "A written slot card, reminder script, and setup checklist for a two-location team.",
    "price": 48,
    "images": ["front.jpg", "in-use.jpg", "contents.jpg", "size.jpg"],
    "attributes": {"material": "cardstock", "count": "50"},
    "stock": 12,
    "reorder_at": 20,
    "commission_rate": 0.12,
    "expected_orders": 30,
}

BANNED = ("cure", "guaranteed viral", "lose weight", "miracle", "risk-free income")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Listing JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def analyze(doc: dict) -> dict:
    issues = []
    title = doc.get("title") or ""
    if not (35 <= len(title) <= 80):
        issues.append(f"title length {len(title)}; aim for 35-80 characters with the product and the buyer")
    desc = doc.get("description") or ""
    if len(desc.split()) < 20:
        issues.append("description is thin; say who it is for and what is in the box")
    hits = [w for w in BANNED if w in (title + " " + desc).lower()]
    if hits:
        issues.append("remove risky claims: " + ", ".join(hits))
    images = doc.get("images") or []
    if len(images) < 4:
        issues.append("use at least 4 images: pack, in use, contents, scale")
    if not doc.get("attributes"):
        issues.append("attributes are empty")
    stock = int(doc.get("stock") or 0)
    reorder = int(doc.get("reorder_at") or 0)
    alert = stock <= reorder
    commission = round(float(doc.get("price") or 0) * float(doc.get("commission_rate") or 0) * int(doc.get("expected_orders") or 0), 2)
    return {
        "company": "{{YOUR_COMPANY}}",
        "issues": issues,
        "inventory_alert": alert,
        "stock": stock,
        "projected_creator_payout": commission,
        "video_brief": [
            "Second 0-2: the product in a hand, not a logo.",
            "Second 2-8: one before-and-after of the job it does.",
            "Last second: price and the shop name spoken once.",
            "Disclose the paid relationship in the caption and on screen.",
        ],
        "approval": "Publish only after {{YOUR_OWNER_NAME}} checks claims against the product policy.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
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
