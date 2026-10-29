#!/usr/bin/env python3
"""A new sprint-tracker row must come from this run's fetch, never the previous row."""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_x_followers as sync


OCT28 = {
    "date": "2026-10-28",
    "clampdown19_followers": 2102,
    "agentscouthq_followers": 12,
    "combined_followers": 2114,
    "source": "live_fetch",
    "fetched_at": "2026-10-28T09:00:00-0700",
}


def tracker_with_oct28():
    return {
        "daily_log": [dict(OCT28)],
        "current": {
            "clampdown19_followers": 2102,
            "agentscouthq_followers": 12,
            "combined_followers": 2114,
            "weekly_page_views_tracker_7d": 482,
        },
    }


class SyncXFollowersTest(unittest.TestCase):
    def test_new_day_uses_fetched_counts_not_the_previous_row(self):
        err = io.StringIO()
        updated = sync.apply_fetch(
            tracker_with_oct28(),
            "2026-10-29",
            {"clampdown19_followers": 2104, "agentscouthq_followers": 13},
            "2026-10-29T09:10:00-0700",
            err,
        )
        row = updated["daily_log"][-1]
        self.assertEqual(row["date"], "2026-10-29")
        self.assertEqual(row["clampdown19_followers"], 2104)
        self.assertEqual(row["agentscouthq_followers"], 13)
        self.assertEqual(row["combined_followers"], 2117)
        self.assertEqual(row["source"], "live_fetch")
        self.assertTrue(row["fetched_at"].startswith("2026-10-29"))
        self.assertEqual(updated["current"]["clampdown19_followers"], 2104)
        self.assertEqual(updated["current"]["agentscouthq_followers"], 13)
        self.assertEqual(updated["current"]["weekly_page_views_tracker_7d"], 482)
        self.assertEqual(updated["daily_log"][0]["clampdown19_followers"], 2102)
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(sync.audit_tracker(updated), [])

    def test_missing_fetch_does_not_append_a_copy(self):
        before = tracker_with_oct28()
        with self.assertRaises(sync.FetchError):
            sync.apply_fetch(before, "2026-10-29", {}, "2026-10-29T09:10:00-0700")
        self.assertEqual(before["daily_log"], [OCT28])
        with self.assertRaises(sync.FetchError):
            sync.build_row("2026-10-29", {"clampdown19_followers": 2102}, "2026-10-29T09:10:00-0700")

    def test_failed_main_does_not_write_the_tracker(self):
        def boom():
            raise sync.FetchError("AgentScoutHQ: live follower count was not in the response")

        before = sync.TRACKER.read_bytes() if sync.TRACKER.exists() else None
        code = sync.main(fetch=boom)
        after = sync.TRACKER.read_bytes() if sync.TRACKER.exists() else None
        self.assertEqual(code, 1)
        self.assertEqual(after, before)

    def test_unchanged_live_counts_warn_but_are_not_copied(self):
        err = io.StringIO()
        updated = sync.apply_fetch(
            tracker_with_oct28(),
            "2026-10-29",
            {"clampdown19_followers": 2102, "agentscouthq_followers": 12},
            "2026-10-29T09:10:00-0700",
            err,
        )
        row = updated["daily_log"][-1]
        self.assertIn("WARNING:", err.getvalue())
        self.assertIn("were not copied", err.getvalue())
        self.assertEqual(row["source"], "live_fetch")
        self.assertTrue(row["fetched_at"].startswith("2026-10-29"))
        self.assertNotEqual(row["fetched_at"], OCT28["fetched_at"])
        self.assertEqual(sync.audit_tracker(updated), [])

    def test_audit_rejects_a_row_copied_from_the_previous_day(self):
        copied = tracker_with_oct28()
        cloned = dict(OCT28)
        cloned["date"] = "2026-10-29"
        copied["daily_log"].append(cloned)
        problems = sync.audit_tracker(copied)
        self.assertTrue(any("fetched_at" in line and "2026-10-29" in line for line in problems))

        nulled = tracker_with_oct28()
        nulled["daily_log"].append(
            {
                "date": "2026-10-29",
                "clampdown19_followers": None,
                "agentscouthq_followers": None,
                "source": "live_fetch",
                "fetched_at": "2026-10-29T09:10:00-0700",
            }
        )
        self.assertTrue(any("missing a live follower count" in line for line in sync.audit_tracker(nulled)))


if __name__ == "__main__":
    unittest.main()
