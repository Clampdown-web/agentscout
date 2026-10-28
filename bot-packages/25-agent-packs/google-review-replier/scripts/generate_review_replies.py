#!/usr/bin/env python3
"""Draft review replies and a velocity snapshot for {{YOUR_COMPANY}}.

Thanks people by name, moves complaints to a private channel, and refuses
review incentives. It writes drafts. A person posts them.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

SAMPLE = [
    {"date": "2026-04-01", "author": "Priya", "stars": "5", "text": "The technician arrived on time and explained the bill."},
    {"date": "2026-04-02", "author": "Jon", "stars": "2", "text": "Waited 40 minutes and nobody called."},
    {"date": "2026-04-03", "author": "Sam", "stars": "1", "text": "This was unsafe and I want a lawyer."},
]

BANNED = ("discount if you", "gift card", "change your review", "remove your review", "five stars and")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="CSV with date, author, stars, text")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--keyword", default="{{YOUR_COMPANY}}", help="Local term to mention once, naturally")
    return p


def reply(row: dict, keyword: str) -> dict:
    stars = int(row["stars"])
    author = row["author"].strip() or "there"
    text = row["text"].strip()
    if any(w in text.lower() for w in ("lawyer", "sue", "illegal", "injury", "unsafe")):
        tone = "escalate"
        body = (
            f"Hi {author}, thank you for telling us. This needs a person, not a public thread. "
            f"Please contact {{{{YOUR_SUPPORT_EMAIL}}}} so {{{{YOUR_OWNER_NAME}}}} can look at it directly."
        )
    elif stars >= 4:
        tone = "thanks"
        body = (
            f"Hi {author}, thank you for mentioning the specifics. "
            f"The team at {keyword} is glad the visit was clear. We will pass this to the people who did the work."
        )
    else:
        tone = "recover"
        body = (
            f"Hi {author}, we are sorry the visit missed the mark. "
            f"Please email {{{{YOUR_SUPPORT_EMAIL}}}} with the date and we will make it right offline."
        )
    flags = [phrase for phrase in BANNED if phrase in body.lower()]
    return {"author": author, "stars": stars, "tone": tone, "draft": body, "policy_flags": flags}


def analyze(rows: list[dict], keyword: str) -> dict:
    drafts = [reply(row, keyword) for row in rows]
    by_star = Counter(int(r["stars"]) for r in rows)
    dates = sorted({r["date"][:10] for r in rows if r.get("date")})
    return {
        "company": "{{YOUR_COMPANY}}",
        "drafts": drafts,
        "star_counts": dict(sorted(by_star.items())),
        "review_days": dates,
        "velocity_note": f"{len(rows)} reviews across {len(dates) or 1} day(s). Reply inside two days.",
        "rules": [
            "Use the reviewer's name and one concrete detail.",
            "Do not stuff the city or service keyword more than once.",
            "Never offer a perk for editing or deleting a review.",
            "Move billing, safety, and legal threads to {{YOUR_SUPPORT_EMAIL}}.",
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
    report = analyze(rows, args.keyword)
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
