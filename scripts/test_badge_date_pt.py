#!/usr/bin/env python3
"""TASK-22 (Nov 18 2026): the homepage "Links checked" badge date is Pacific time.

Regression test for the Nov 19 bug: at 8:17 PM PT on Nov 18 the badge read
"Links checked Nov 19, 2026" because two tools carried verified=2026-11-19,
stamped with the container's UTC date while it was still Nov 18 in Pacific.
The link-check card on the same page said November 18, so the two disagreed.

Guards:
- no verified date in tools.json is after today in America/Los_Angeles
  (a UTC-stamped evening edit would be tomorrow in PT);
- the eyebrow badge in index.html shows exactly max(verified), formatted
  in Pacific, and agrees with api/tools.json and api/home.json.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

PT = ZoneInfo("America/Los_Angeles")


def pt_today():
    return datetime.datetime.now(PT).date()


def fmt(d):
    return d.strftime("%b %-d, %Y")


class BadgeDatePtTest(unittest.TestCase):
    def test_no_verified_date_after_pt_today(self):
        tools = json.load(open("tools.json"))
        today = pt_today()
        future = [
            (x.get("slug"), x.get("verified"))
            for x in tools
            if (x.get("verified") or "") > today.isoformat()
        ]
        self.assertEqual(
            future, [], f"verified dates after PT today {today}: {future[:5]}"
        )

    def test_badge_matches_max_verified(self):
        tools = json.load(open("tools.json"))
        last = max((x.get("verified") or "") for x in tools)
        self.assertRegex(last, r"^\d{4}-\d{2}-\d{2}$")
        expected = fmt(datetime.date.fromisoformat(last))
        html = open("index.html", encoding="utf-8").read()
        m = re.search(
            r'id="s-eyebrow">[\d,]+ tools · Links checked ([^<]+)', html
        )
        self.assertIsNotNone(m, "homepage eyebrow badge not found")
        self.assertEqual(
            m.group(1),
            expected,
            f"badge shows {m.group(1)} but max(verified) is {last} ({expected})",
        )

    def test_api_feeds_agree_with_max_verified(self):
        tools = json.load(open("tools.json"))
        last = max((x.get("verified") or "") for x in tools)
        for path in ("api/tools.json", "api/stats.json", "api/home.json"):
            with self.subTest(path=path):
                data = json.load(open(path))
                self.assertEqual(
                    data.get("last_checked"),
                    last,
                    f"{path} last_checked is {data.get('last_checked')}, "
                    f"expected max(verified) {last}",
                )


if __name__ == "__main__":
    unittest.main()
