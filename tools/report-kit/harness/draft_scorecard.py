#!/usr/bin/env python3
"""Start a scorecard from a transcript.

Latency and counts are copied from the transcript. The score, verdict, fixes,
and other written judgments are left empty for a person to fill in. This
script does not invent them, and it does not print session tokens.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redact import redact_obj  # noqa: E402


def draft(transcript: dict) -> dict:
    transcript = redact_obj(transcript)
    timings = transcript.get("timings_ms") or {}
    facts = []
    for name, row in timings.items():
        if not isinstance(row, dict):
            continue
        facts.append({
            "step": name,
            "p50_ms": row.get("p50"),
            "min_ms": row.get("min"),
            "max_ms": row.get("max"),
            "n": row.get("n"),
        })
    target = transcript.get("target") or {}
    return {
        "product_title": "MCP Server Test Report",
        "sample": False,
        "score": None,
        "score_max": 100,
        "tested_display": "",
        "timezone_label": transcript.get("timezone_note") or "",
        "verdict": "",
        "cover_blurb": "",
        "scorecard": [],
        "top_fixes": [],
        "further_improvements": [],
        "further_note": "",
        "methodology": [],
        "out_of_scope": [],
        "disclaimer": "",
        "whats_great": "",
        "what_this_means": [],
        "badge_date": "",
        "next_step": {
            "title": "Next step",
            "body": "",
            "link_label": "booking link placeholder",
        },
        "badge_disclaimer": "This badge is a dated test result, not an AgentScout endorsement. Scores can change as the server is updated.",
        "transcript_facts": {
            "endpoint": target.get("endpoint") or "",
            "listed_name": target.get("listed_name") or "",
            "tool_count": transcript.get("tool_count"),
            "runs": transcript.get("runs"),
            "latency": facts,
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Draft a scorecard JSON from a redacted transcript.")
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
    payload = draft(transcript)
    text = json.dumps(payload, indent=2)
    if "mcp-session-id" in text and "[redacted]" not in text:
        raise SystemExit("refusing to write a scorecard that still contains a session token")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
