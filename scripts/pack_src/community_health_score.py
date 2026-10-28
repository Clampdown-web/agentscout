#!/usr/bin/env python3
"""Score community health for {{YOUR_COMPANY}} from a member activity CSV.

Measures lurkers, a simple 14-day active rate, and new-member silence.
It suggests prompts. It does not message members.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

SAMPLE = [
    {"member": "A", "joined": "2026-03-01", "last_active": "2026-04-05", "posts": "4", "comments": "10"},
    {"member": "B", "joined": "2026-04-01", "last_active": "2026-04-01", "posts": "0", "comments": "0"},
    {"member": "C", "joined": "2026-01-10", "last_active": "2026-02-01", "posts": "1", "comments": "0"},
    {"member": "D", "joined": "2026-02-02", "last_active": "2026-04-04", "posts": "0", "comments": "6"},
]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Member CSV")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--as-of", default="2026-04-06")
    return p


def analyze(rows: list[dict], as_of: date) -> dict:
    lurkers = []
    quiet_new = []
    active = 0
    for row in rows:
        last = datetime.strptime(row["last_active"][:10], "%Y-%m-%d").date()
        joined = datetime.strptime(row["joined"][:10], "%Y-%m-%d").date()
        posts = int(row.get("posts") or 0)
        comments = int(row.get("comments") or 0)
        if (as_of - last).days <= 14 and (posts + comments) > 0:
            active += 1
        if posts + comments == 0:
            lurkers.append(row["member"])
        if (as_of - joined).days <= 14 and (as_of - last).days >= 3 and posts + comments == 0:
            quiet_new.append(row["member"])
    total = max(1, len(rows))
    score = round(100 * active / total, 1)
    return {
        "company": "{{YOUR_COMPANY}}",
        "as_of": as_of.isoformat(),
        "members": len(rows),
        "active_14d": active,
        "health_score": score,
        "lurkers": lurkers,
        "quiet_new_members": quiet_new,
        "prompts": [
            "What did a customer ask you this week that the FAQ still misses?",
            "Show one photo of the work, with the lesson in a single sentence.",
            "Which step in onboarding felt slower than it should?",
        ],
        "onboarding": [
            "Day 0: welcome and the code of conduct.",
            "Day 2: one easy introduction prompt.",
            "Day 7: ask if they found the answer they joined for.",
        ],
        "moderation": "Warn in public only for the rule that was broken. Move harassment and personal data to {{YOUR_SUPPORT_EMAIL}}.",
    }


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    dry = args.dry_run or args.sample or not args.input
    if dry:
        rows = SAMPLE
    else:
        with open(args.input, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    report = analyze(rows, date.fromisoformat(args.as_of))
    report["dry_run"] = dry
    payload = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
