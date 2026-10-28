#!/usr/bin/env python3
"""Score social hooks and format a short thread for {{YOUR_COMPANY}}.

Looks for a number, a specific noun, and a curiosity gap. It does not post.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = {
    "platform": "x",
    "hooks": [
        "We cut quote-to-calendar from 6 days to 1 afternoon.",
        "Big news coming soon!!!",
        "The receptionist script that stopped three no-shows last week.",
    ],
}

LIMITS = {"x": 280, "threads": 500, "linkedin": 3000, "instagram": 2200}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="JSON with platform and hooks")
    p.add_argument("--output", help="JSON report path")
    return p


def score(hook: str) -> dict:
    points = 0
    notes = []
    if re.search(r"\d", hook):
        points += 30
        notes.append("contains a number")
    if len(hook.split()) <= 18:
        points += 20
        notes.append("short enough to read once")
    else:
        notes.append("trim the first line")
    if any(w in hook.lower() for w in ("how", "why", "stopped", "cut", "before", "without")):
        points += 25
        notes.append("opens a gap or a change")
    if hook.count("!") > 1 or "coming soon" in hook.lower():
        points -= 20
        notes.append("hype without a fact")
    nouns = re.findall(r"[A-Za-z]{5,}", hook)
    if len(nouns) >= 3:
        points += 15
        notes.append("specific vocabulary")
    return {"hook": hook, "score": max(0, min(100, points)), "notes": notes}


def analyze(doc: dict) -> dict:
    platform = (doc.get("platform") or "x").lower()
    scored = sorted((score(h) for h in doc.get("hooks", [])), key=lambda r: r["score"], reverse=True)
    winner = scored[0]["hook"] if scored else ""
    thread = []
    if winner:
        thread = [
            winner,
            "What changed: one owner, one written slot, one reminder.",
            "If you want the checklist, reply with the word slot.",
        ]
    limit = LIMITS.get(platform, 280)
    return {
        "company": "{{YOUR_COMPANY}}",
        "platform": platform,
        "char_limit": limit,
        "over_limit": [h for h in thread if len(h) > limit],
        "ranked": scored,
        "thread": thread,
        "utm": "Add ?utm_source=" + platform + "&utm_medium=organic&utm_campaign={{YOUR_COMPANY}} before you publish.",
        "approval": "Do not post until {{YOUR_OWNER_NAME}} accepts the winner.",
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
