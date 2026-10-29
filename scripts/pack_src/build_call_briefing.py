#!/usr/bin/env python3
"""Build a pre-call briefing and reminder plan for {{YOUR_COMPANY}}.

Proposes slots in the prospect's timezone offset and drafts the no-show
sequence. It does not write to a calendar.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SAMPLE = {
    "prospect": "Alex Kim",
    "company": "Northwind",
    "timezone_offset": "-07:00",
    "goal": "See if same-day booking fits a two-location clinic",
    "notes": "Hiring a receptionist. Asked about no-show fees.",
    "qualified": True,
    "anchor": "2026-04-07T16:00:00+00:00",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true", help="Run built-in self-test sample and exit 0")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Lead JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def parse_offset(text: str) -> timezone:
    sign = 1 if text.startswith("+") else -1
    hours, minutes = text[1:].split(":")
    return timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))


def analyze(doc: dict) -> dict:
    anchor = datetime.fromisoformat(doc["anchor"])
    tz = parse_offset(doc.get("timezone_offset") or "+00:00")
    local = anchor.astimezone(tz)
    slots = []
    for hours in (24, 48, 72):
        start = local + timedelta(hours=hours)
        if start.weekday() >= 5:
            start += timedelta(days=7 - start.weekday())
        start = start.replace(hour=10, minute=0, second=0, microsecond=0)
        slots.append({"local": start.isoformat(), "utc": start.astimezone(timezone.utc).isoformat(), "length_min": 20})
    return {
        "company": "{{YOUR_COMPANY}}",
        "prospect": doc["prospect"],
        "their_company": doc.get("company", ""),
        "qualified": bool(doc.get("qualified")),
        "speed_to_lead": "Reply inside five minutes of the first inquiry while the context is still warm.",
        "slots": slots[:3],
        "briefing": {
            "goal": doc.get("goal", ""),
            "notes": doc.get("notes", ""),
            "open_with": f"Confirm why {doc['prospect']} took the meeting in their words before you demo.",
            "do_not": "Do not quote a custom discount live. Park it for {{YOUR_OWNER_NAME}}.",
        },
        "reminders": [
            {"when": "24h before", "channel": "email"},
            {"when": "1h before", "channel": "sms or email"},
        ],
        "no_show": "Wait 10 minutes, send one reschedule note with two fresh slots, then stop.",
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
