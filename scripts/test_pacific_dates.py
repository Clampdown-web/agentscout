#!/usr/bin/env python3
"""Builders must stamp displayed dates in America/Los_Angeles.

Fails if a site builder takes 'now' in UTC, uses a naive date, or pretends a
fixed UTC-7 offset is Pacific. Parsing an incoming UTC instant so it can be
shown in Pacific is allowed. News day names are not dates this test checks.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Site builders and the scripts that stamp public dates. Pack samples and tests
# are not the daily build.
SCAN = [p for p in ROOT.glob("build_*.py")]
SCAN += [
    ROOT / "daily_update.py",
    ROOT / "scripts" / "update_news.py",
    ROOT / "scripts" / "indexnow_ping.py",
    ROOT / "scripts" / "morning_pipeline.py",
    ROOT / "scripts" / "content_check.py",
    ROOT / "scripts" / "mcp_response_rate.py",
    ROOT / "scripts" / "make_animated_infographics.py",
    ROOT / "scripts" / "start_here.py",
]

FORBIDDEN = (
    (re.compile(r"\.utcnow\("), "datetime.utcnow()"),
    (re.compile(r"(?<![\w.])date\.today\("), "date.today()"),
    (re.compile(r"datetime\.date\.today\("), "datetime.date.today()"),
    (re.compile(r"time\.gmtime"), "time.gmtime"),
    (re.compile(r"datetime\.now\(\)"), "datetime.now() with no timezone"),
    (re.compile(r"datetime\.datetime\.now\(\)"), "datetime.datetime.now() with no timezone"),
    (re.compile(r"now\(\s*(?:datetime\.)?timezone\.utc\s*\)"), "now(timezone.utc)"),
    (re.compile(r"now\(\s*dt\.timezone\.utc\s*\)"), "now(dt.timezone.utc)"),
    (re.compile(r"timedelta\(\s*hours\s*=\s*-7\s*\)"), "fixed UTC-7 offset used as Pacific"),
    (re.compile(r"timedelta\(\s*hours\s*=\s*-8\s*\)"), "fixed UTC-8 offset used as Pacific"),
)


def _code(text: str) -> str:
    """Drop comments so a note about UTC is not a date stamp."""
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            line = re.sub(r"\s+#.*$", "", line)
        out.append(line)
    return "\n".join(out)


class PacificDateTest(unittest.TestCase):
    def test_builders_do_not_stamp_naive_or_utc_dates(self):
        problems = []
        for path in SCAN:
            self.assertTrue(path.is_file(), path)
            text = _code(path.read_text(encoding="utf-8"))
            rel = path.relative_to(ROOT).as_posix()
            for pattern, label in FORBIDDEN:
                if pattern.search(text):
                    problems.append(f"{rel}: {label}")
        self.assertEqual(problems, [], "displayed dates must use America/Los_Angeles:\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
