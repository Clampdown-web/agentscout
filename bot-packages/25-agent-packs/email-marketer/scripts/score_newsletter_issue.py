#!/usr/bin/env python3
"""Score a newsletter issue for {{YOUR_COMPANY}} before it is scheduled.

Checks subject and preview length, a single primary link story, the
unsubscribe path, and whether a plain-text twin exists.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SAMPLE = {
    "subject_a": "Your Tuesday slot list is short",
    "subject_b": "Newsletter",
    "preview": "Three open hours and the one job that fills them.",
    "html": "<p>Hi there,</p><p>Three hours are open Thursday. <a href=\"https://{{YOUR_DOMAIN}}/book\">Hold one</a>.</p><p><a href=\"https://{{YOUR_DOMAIN}}/unsub\">Unsubscribe</a></p>",
    "text": "Three hours are open Thursday. Hold one: https://{{YOUR_DOMAIN}}/book\nUnsubscribe: https://{{YOUR_DOMAIN}}/unsub",
    "segment": "engaged-30d",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    p.add_argument("--input", help="Issue JSON")
    p.add_argument("--output", help="JSON report path")
    return p


def subject_score(subject: str) -> dict:
    n = len(subject.strip())
    issues = []
    if not (28 <= n <= 58):
        issues.append(f"{n} characters; aim for 28-58")
    if subject.strip().lower() in {"newsletter", "update", "hi"}:
        issues.append("subject is generic")
    if subject.count("!") > 1 or subject.isupper():
        issues.append("subject looks like a shout")
    return {"subject": subject, "characters": n, "issues": issues}


def analyze(doc: dict) -> dict:
    html = doc.get("html") or ""
    text = doc.get("text") or ""
    links = re.findall(r'href=["\']([^"\']+)', html, flags=re.I)
    text_links = re.findall(r"https?://\S+", text)
    preview = doc.get("preview") or ""
    return {
        "company": "{{YOUR_COMPANY}}",
        "segment": doc.get("segment", "unspecified"),
        "subjects": [subject_score(doc.get("subject_a", "")), subject_score(doc.get("subject_b", ""))],
        "preview_characters": len(preview),
        "preview_ok": 35 <= len(preview) <= 90,
        "html_links": links,
        "plain_text_present": bool(text.strip()),
        "plain_links_match": set(links) <= set(text_links) or not links,
        "unsubscribe_present": "unsub" in html.lower() or "unsubscribe" in (html + text).lower(),
        "architecture": [
            "One story, one proof, one button.",
            "Preview text should finish the subject, not repeat it.",
            "Send a win-back only to people quiet for 90 days, then sunset.",
        ],
        "approval": "Schedule only after {{YOUR_OWNER_NAME}} reads the winner subject.",
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
