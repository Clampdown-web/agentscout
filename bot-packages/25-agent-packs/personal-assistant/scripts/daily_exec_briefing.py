#!/usr/bin/env python3
"""Assemble a morning briefing for {{YOUR_OWNER_NAME}} at {{YOUR_COMPANY}}.

Sorts inbox notes with an Eisenhower grid, flags overlapping calendar holds,
and lists a travel or task checklist. It never deletes mail.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SAMPLE = {
    "date": "2026-04-06",
    "inbox": [
        {"id": "m1", "subject": "Contract redline due today", "urgent": True, "important": True},
        {"id": "m2", "subject": "Newsletter draft for review", "urgent": False, "important": True},
        {"id": "m3", "subject": "Vendor webinar invite", "urgent": False, "important": False},
    ],
    "calendar": [
        {"title": "Pipeline review", "start": "2026-04-06T15:00:00", "end": "2026-04-06T15:45:00"},
        {"title": "Customer call", "start": "2026-04-06T15:30:00", "end": "2026-04-06T16:00:00"},
    ],
    "trips": [{"city": "Austin", "date": "2026-04-09", "open": "Hotel confirmation still missing"}],
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Briefing JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def grid(item: dict) -> str:
    if item.get("urgent") and item.get("important"):
        return "do"
    if item.get("important"):
        return "schedule"
    if item.get("urgent"):
        return "delegate"
    return "defer"


def overlaps(a: dict, b: dict) -> bool:
    a0, a1 = datetime.fromisoformat(a["start"]), datetime.fromisoformat(a["end"])
    b0, b1 = datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"])
    return a0 < b1 and b0 < a1


def analyze(doc: dict) -> dict:
    inbox = [{**item, "bucket": grid(item)} for item in doc.get("inbox", [])]
    events = doc.get("calendar", [])
    conflicts = []
    for i, event in enumerate(events):
        for other in events[i + 1:]:
            if overlaps(event, other):
                conflicts.append([event["title"], other["title"]])
    return {
        "company": "{{YOUR_COMPANY}}",
        "owner": "{{YOUR_OWNER_NAME}}",
        "date": doc.get("date"),
        "inbox": inbox,
        "conflicts": conflicts,
        "travel_checklist": doc.get("trips", []),
        "rules": [
            "Archive is allowed. Delete is not, unless {{YOUR_OWNER_NAME}} says so in writing.",
            "Put do-now items above the meeting list.",
            "A conflict is a proposal to move the lower-priority hold, not an automatic decline.",
        ],
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
