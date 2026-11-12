#!/usr/bin/env python3
"""The health dot follows the live share, not a single down server.

Green at or above 98% live, amber from 90% up to 98%, red below 90% or when
the stored check is older than 36 hours. The down chip and the Down right now
pills stay, so a single outage is still named.
"""
from __future__ import annotations

import atexit
import json
import os
import re
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import build_seo_trim
import build_status

PT = ZoneInfo("America/Los_Angeles")


def tearDownModule():
    # build_document imports builders that register site-wide exit hooks.
    atexit._clear()


def _dot(html):
    found = re.search(r'class="(vc-dot[^"]*)"', html)
    if not found:
        raise AssertionError("no status dot in " + html[:240])
    return found.group(1)


def _pages(live, down, checked):
    servers = [{"status": "live", "slug": f"live-{i}", "name": f"Live {i}"} for i in range(live)]
    servers += [{"status": "down", "slug": f"down-{i}", "name": f"Down {i}"} for i in range(down)]
    doc = {"catalog": {"mcp_last_checked": checked, "history": []}, "servers": servers}
    return build_status.home_slim(doc), build_status.panel(doc, servers, "", "Verification")


class StatusDotTest(unittest.TestCase):
    def test_thresholds_are_shared(self):
        self.assertEqual(build_status.DOT_LIVE_OK_PCT, 98)
        self.assertEqual(build_status.DOT_LIVE_WARN_PCT, 90)
        self.assertEqual(build_status.DOT_STALE, timedelta(hours=36))

    def test_three_states_and_the_stale_check(self):
        now = datetime(2026, 11, 10, 12, 0, tzinfo=PT)
        fresh = "2026-11-10 07:00"
        dot = build_status.status_dot_class
        self.assertEqual(dot(98, 100, fresh, now), "vc-dot")
        self.assertEqual(dot(99, 100, fresh, now), "vc-dot")
        self.assertEqual(dot(1064, 1065, fresh, now), "vc-dot")
        self.assertEqual(dot(979, 1000, fresh, now), "vc-dot vc-warn-dot")
        self.assertEqual(dot(90, 100, fresh, now), "vc-dot vc-warn-dot")
        self.assertEqual(dot(89, 100, fresh, now), "vc-dot vc-dn")
        self.assertEqual(dot(0, 1, fresh, now), "vc-dot vc-dn")
        self.assertEqual(dot(0, 0, fresh, now), "vc-dot")
        self.assertEqual(dot(50, 100, "", now), "vc-dot vc-dn")
        self.assertEqual(dot(100, 100, "", now), "vc-dot")
        exact = (now - timedelta(hours=36)).strftime("%Y-%m-%d %H:%M")
        over = (now - timedelta(hours=36, minutes=1)).strftime("%Y-%m-%d %H:%M")
        self.assertEqual(dot(100, 100, exact, now), "vc-dot")
        self.assertEqual(dot(100, 100, over, now), "vc-dot vc-dn")
        self.assertEqual(dot(100, 100, "2026-11-10", datetime(2026, 11, 12, 11, 58, tzinfo=PT)), "vc-dot")
        self.assertEqual(dot(100, 100, "2026-11-10", datetime(2026, 11, 12, 12, 0, tzinfo=PT)), "vc-dot vc-dn")

    def test_rendered_pages_use_the_helper_for_every_dot(self):
        fresh = datetime.now(PT).strftime("%Y-%m-%d %H:%M")
        home, panel = _pages(98, 2, fresh)
        self.assertEqual(_dot(home), "vc-dot")
        self.assertEqual(_dot(panel), "vc-dot")
        self.assertIn("<b>2</b> down", panel)
        self.assertIn("Down right now", panel)
        self.assertIn("Down 0", panel)

        home, panel = _pages(90, 10, fresh)
        self.assertEqual(_dot(home), "vc-dot vc-warn-dot")
        self.assertEqual(_dot(panel), "vc-dot vc-warn-dot")
        self.assertIn("<b>10</b> down", panel)
        self.assertIn("Down right now", panel)

        home, panel = _pages(80, 20, fresh)
        self.assertEqual(_dot(home), "vc-dot vc-dn")
        self.assertEqual(_dot(panel), "vc-dot vc-dn")
        self.assertIn("<b>20</b> down", panel)

        home, panel = _pages(100, 0, "2020-01-01 00:00")
        self.assertEqual(_dot(home), "vc-dot vc-dn")
        self.assertEqual(_dot(panel), "vc-dot vc-dn")
        self.assertIn("<b>0</b> down", panel)
        self.assertNotIn("Down right now", panel)

        self.assertEqual(_dot(build_status.tool_rows({"status": "live", "last_checked": fresh})), "vc-dot")
        self.assertEqual(_dot(build_status.tool_rows({"status": "down", "last_checked": fresh})), "vc-dot vc-dn")
        self.assertEqual(
            _dot(build_status.tool_rows({"status": "live", "last_checked": "2020-01-01 00:00"})),
            "vc-dot vc-dn",
        )
        today = datetime.now(PT).strftime("%Y-%m-%d")
        self.assertEqual(_dot(build_seo_trim.dir_rows({"verified": "2020-01-01"}, today)), "vc-dot")
        self.assertEqual(_dot(build_seo_trim.dir_rows({"verified": today}, "2020-01-01")), "vc-dot vc-dn")

    def test_published_catalog_is_green_on_the_day_of_the_check(self):
        doc = build_status.build_document(json.load(open("tools.json")))
        cat = doc["catalog"]
        when = datetime(2026, 11, 10, 12, 0, tzinfo=PT)
        dot = build_status.status_dot_class(cat["live"], cat["checked"], cat.get("mcp_last_checked") or "", when)
        self.assertGreater(cat["checked"], 0)
        self.assertGreaterEqual(cat["live"] * 100, cat["checked"] * build_status.DOT_LIVE_OK_PCT)
        self.assertEqual(dot, "vc-dot")
        home = build_status.home_slim(doc)
        panel = build_status.panel(doc, doc["servers"], "../", "Verification")
        live_dot = build_status.status_dot_class(cat["live"], cat["checked"], cat.get("mcp_last_checked") or "")
        self.assertEqual(_dot(home), live_dot)
        self.assertEqual(_dot(panel), live_dot)
        self.assertIn(f"<b>{cat['live']:,} of {cat['checked']:,}</b>", home)
        self.assertIn(f"<b>{cat['down']}</b> down", panel)
        if cat["down"]:
            self.assertIn("Down right now", panel)
            self.assertIn('class="vc-pill"', panel)

    def test_styles_define_the_amber_dot_without_a_pulse(self):
        for name in ("styles.css", "home-mobile.css"):
            css = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(".vc-dot.vc-warn-dot{background:#fbbf24", css)
            self.assertIn("animation:none!important", css)
            self.assertIn("@keyframes vc-live", css)


if __name__ == "__main__":
    unittest.main()
