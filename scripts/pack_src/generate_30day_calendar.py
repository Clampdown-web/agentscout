#!/usr/bin/env python3
"""Build a 30-day editorial calendar for {{YOUR_COMPANY}}.

Maps pillars to buyer stages and a repurposing matrix. It does not publish.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SAMPLE = {
    "start": "2026-04-06",
    "pillars": ["proof", "how-to", "offer", "behind-the-scenes"],
    "offer": "same-day booking",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Calendar settings JSON")
    p.add_argument("--output", help="JSON report path")
    return p


STAGES = ["problem-aware", "solution-aware", "product-aware", "ready-to-buy"]
FORMATS = ["short post", "email note", "15s video", "faq answer"]


def analyze(doc: dict) -> dict:
    start = date.fromisoformat(doc.get("start") or "2026-04-06")
    pillars = doc.get("pillars") or ["proof", "how-to", "offer"]
    days = []
    for i in range(30):
        current = start + timedelta(days=i)
        pillar = pillars[i % len(pillars)]
        stage = STAGES[i % len(STAGES)]
        days.append({
            "date": current.isoformat(),
            "weekday": current.strftime("%A"),
            "pillar": pillar,
            "buyer_stage": stage,
            "format": FORMATS[i % len(FORMATS)],
            "working_title": f"{pillar}: {doc.get('offer', 'the offer')} for a {stage} buyer",
            "repurpose": [
                "Turn the post into a 5-line email.",
                "Cut one sentence into a caption.",
                "Save the question as a page section if it repeats.",
            ],
        })
    clusters = {}
    for pillar in pillars:
        clusters[pillar] = [d["date"] for d in days if d["pillar"] == pillar][:4]
    return {
        "company": "{{YOUR_COMPANY}}",
        "days": days,
        "cluster_starts": clusters,
        "rules": [
            "One pillar owns the week so the audience can tell the themes apart.",
            "Ready-to-buy pieces stay under 20% of the month.",
            "Refresh a URL that already ranks before you invent a new one.",
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
