#!/usr/bin/env python3
"""Score candidates against a written rubric for {{YOUR_COMPANY}}.

Flags risky language in notes. It never auto-rejects a person and it does
not infer protected traits.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = {
    "role": "Customer coordinator",
    "rubric": [
        {"id": "scheduling", "weight": 40, "evidence": "calendar"},
        {"id": "writing", "weight": 30, "evidence": "email"},
        {"id": "ownership", "weight": 30, "evidence": "example"},
    ],
    "candidates": [
        {"name": "Riley Chen", "evidence": {"calendar": "Ran a 12-person dispatch board", "email": "Clear three-line updates", "example": "Rebuilt the no-show script"}, "notes": "Strong sample."},
        {"name": "Jordan Blake", "evidence": {"calendar": "", "email": "Short notes", "example": ""}, "notes": "Seems too old for the pace."},
    ],
}

RISKY = ("too old", "too young", "pregnant", "accent", "married", "religion", "disability", "origin", "gender")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Rubric JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def analyze(doc: dict) -> dict:
    scored = []
    for person in doc["candidates"]:
        total = 0
        parts = []
        for item in doc["rubric"]:
            text = (person.get("evidence") or {}).get(item["evidence"], "")
            got = item["weight"] if len(text.split()) >= 3 else 0
            total += got
            parts.append({"criterion": item["id"], "points": got, "max": item["weight"], "evidence": text})
        notes = person.get("notes", "")
        flags = [w for w in RISKY if re.search(rf"\b{re.escape(w)}\b", notes.lower())]
        scored.append({
            "name": person["name"],
            "score": total,
            "parts": parts,
            "note_flags": flags,
            "decision": "needs-human-review" if flags or total < 70 else "advance-to-interview",
        })
    return {
        "company": "{{YOUR_COMPANY}}",
        "role": doc.get("role", ""),
        "candidates": scored,
        "interview_prompts": [
            "Walk through the last time a schedule broke. What did you do in the first hour?",
            "Show a message you sent a frustrated customer. What did you leave out on purpose?",
            "Which part of this rubric is weakest in your background, and how would you close it?",
        ],
        "rules": [
            "Score the evidence, not a hunch.",
            "A language flag pauses the file for {{YOUR_OWNER_NAME}}. It is not a rejection reason.",
            "Send a respectful pass note within five business days if you close the file.",
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
