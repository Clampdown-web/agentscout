#!/usr/bin/env python3
"""News ranking keeps a share of slots for the last 24 hours.

The Nov 9 morning run sorted by score, then oldest date, so eight older
higher-scored rows filled every slot. Same-day rows sat further down the list.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_news as news

ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 11, 9, 15, 7, 37, tzinfo=dt.timezone.utc)
FRESH_CUT = "2026-11-08T15:07:37Z"


def item(title, date, score, url=None, source="X News"):
    return {
        "title": title,
        "url": url or "https://example.com/" + title.lower().replace(" ", "-"),
        "date": date,
        "score": score,
        "source": source,
        "tool": None,
    }


def fresh_count(rows, cutoff=FRESH_CUT):
    return sum(1 for row in rows if row["date"] >= cutoff)


class NewsRankTests(unittest.TestCase):
    def test_equal_scores_keep_the_newer_item_first(self):
        ranked = news.rank_candidates([
            item("older", "2026-11-07T08:00:00Z", 5),
            item("newer", "2026-11-08T08:00:00Z", 5),
            item("best", "2026-11-06T18:00:00Z", 6),
        ])
        self.assertEqual([row["title"] for row in ranked], ["best", "newer", "older"])

    def test_dedupe_keeps_the_newer_tie(self):
        kept = news.dedupe([
            item("Same headline about agents", "2026-11-07T08:00:00Z", 3, url="https://example.com/a"),
            item("Same headline about agents", "2026-11-09T08:00:00Z", 3, url="https://example.com/b"),
        ])
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["date"], "2026-11-09T08:00:00Z")

    def test_fresh_share_tracks_how_many_slots_were_requested(self):
        self.assertEqual(news.fresh_slots(8), 4)
        self.assertEqual(news.fresh_slots(5), 3)
        self.assertEqual(news.fresh_slots(1), 1)
        self.assertEqual(news.fresh_slots(0), 0)

    def test_lower_scored_same_day_items_still_take_half_the_slots(self):
        """Nov 9 shape: older rows score 4-5, today's Google News rows score 2."""
        older = [
            ("Duet", "2026-11-07T08:36:33Z", 5),
            ("OpenCode", "2026-11-07T10:19:42Z", 5),
            ("METR", "2026-11-07T13:19:56Z", 5),
            ("Coinbase", "2026-11-08T11:21:05Z", 5),
            ("Oren", "2026-11-06T16:32:53Z", 4),
            ("Cursor", "2026-11-06T16:44:19Z", 4),
            ("Leak", "2026-11-06T22:48:14Z", 4),
            ("Meta", "2026-11-07T19:37:24Z", 4),
        ]
        rows = [item(title, date, score) for title, date, score in older]
        for i, date in enumerate((
            "2026-11-09T09:00:00Z",
            "2026-11-09T11:00:00Z",
            "2026-11-09T12:30:00Z",
            "2026-11-09T13:39:42Z",
        )):
            rows.append(item(f"Google News today {i}", date, 2, source="Google News"))
        old_top = sorted(rows, key=lambda row: (-row["score"], row["date"]))[:8]
        self.assertTrue(all(not row["date"].startswith("2026-11-09") for row in old_top))
        n = 8
        chosen = news.newest_first(news.select_slots(news.dedupe(rows), n, NOW, 72))
        self.assertEqual(len(chosen), n)
        self.assertGreaterEqual(fresh_count(chosen), 4)
        self.assertGreaterEqual(chosen[0]["date"], FRESH_CUT)
        self.assertTrue(chosen[0]["date"].startswith("2026-11-09"))
        self.assertEqual(fresh_count(chosen), 4)

    def test_odd_slot_count_still_reserves_at_least_half(self):
        n = 5
        rows = [item(f"old {i}", f"2026-11-07T0{i}:00:00Z", 9) for i in range(n)]
        rows += [item(f"today {i}", f"2026-11-09T0{i}:30:00Z", 1, source="Google News") for i in range(n)]
        chosen = news.select_slots(news.dedupe(rows), n, NOW, 72)
        self.assertEqual(len(chosen), n)
        self.assertEqual(fresh_count(chosen), 3)

    def test_fresh_rows_can_fill_more_than_half_when_they_rank_higher(self):
        n = 6
        rows = [item(f"today {i}", f"2026-11-09T0{i}:10:00Z", 8) for i in range(n)]
        rows += [item(f"old {i}", f"2026-11-07T0{i}:10:00Z", 2) for i in range(n)]
        chosen = news.select_slots(news.dedupe(rows), n, NOW, 72)
        self.assertEqual(len(chosen), n)
        self.assertTrue(all(row["date"].startswith("2026-11-09") for row in chosen))

    def test_one_fresh_row_leaves_the_rest_to_the_wider_window(self):
        n = 8
        rows = [item("only today", "2026-11-09T12:00:00Z", 1, source="Google News")]
        rows += [item(f"old {i}", f"2026-11-07T0{i}:00:00Z", 4) for i in range(n)]
        chosen = news.select_slots(news.dedupe(rows), n, NOW, 72)
        self.assertEqual(len(chosen), n)
        self.assertEqual(fresh_count(chosen), 1)

    def test_offline_dry_run_reads_the_cache_first_and_writes_nothing(self):
        rows = [item(f"old {i}", f"2026-11-07T0{i}:00:00Z", 5) for i in range(8)]
        rows += [item(f"Today story {i}", f"2026-11-09T1{i}:00:00Z", 1, source="Google News") for i in range(4)]
        news_bytes = (ROOT / "news.json").read_bytes()
        archive_bytes = (ROOT / "news-archive.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "x_items.json"
            cache.write_text(json.dumps(rows), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            def boom(url):
                raise AssertionError("offline run fetched " + url)
            original = news.fetch
            news.fetch = boom
            try:
                with redirect_stdout(out), redirect_stderr(err):
                    news.main(["--x", str(cache), "--offline", "--dry-run", "--hours", "72", "--n", "8"], now=NOW)
            finally:
                news.fetch = original
        self.assertEqual((ROOT / "news.json").read_bytes(), news_bytes)
        self.assertEqual((ROOT / "news-archive.json").read_bytes(), archive_bytes)
        self.assertEqual(err.getvalue(), "")
        text = out.getvalue()
        self.assertIn("4 in the last 24h (dry-run)", text)
        lines = [line for line in text.splitlines() if line.startswith("2026-")]
        self.assertEqual(len(lines), 8)
        self.assertTrue(all(line.startswith("2026-11-09") for line in lines[:4]))
        self.assertTrue(lines[4].startswith("2026-11-07"))

    def test_stale_cache_warns_and_still_ranks(self):
        rows = [item(f"old {i}", f"2026-11-07T0{i}:00:00Z", 5) for i in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "x_items.json"
            cache.write_text(json.dumps(rows), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                news.main(["--x", str(cache), "--offline", "--dry-run", "--n", "8"], now=NOW)
        self.assertIn("refresh scripts/x_items.json", err.getvalue())
        self.assertIn("0 in the last 24h", out.getvalue())


if __name__ == "__main__":
    unittest.main()
