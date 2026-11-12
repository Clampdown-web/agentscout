#!/usr/bin/env python3
"""Badge wording and the Responds sort. No network and no tool calls."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import mcp_response_rate as mrr
import build_rich

BADGE = re.compile(r'<span class="b" data-mcp-health="1">([^<]*)</span>')


def _row(display, **extra):
    row = {"display": display}
    row.update(extra)
    return row


class BadgeWordingTests(unittest.TestCase):
    def test_wording_comes_only_from_badge_text(self):
        cases = [
            _row("rate", ok_30d=12, n_30d=14, rate_30d=0.857),
            _row("needs_auth", auth_30d=4),
            _row("local_only"),
            _row("insufficient", ok_30d=2, n_30d=2, rate_30d=1.0),
            None,
        ]
        for row in cases:
            html = mrr.badge_html(row)
            text = mrr.badge_text(row if isinstance(row, dict) else None)
            self.assertEqual(BADGE.fullmatch(html).group(1), text)
            self.assertNotIn("%", text)
            self.assertNotIn("down", text.lower())

    def test_missing_slug_is_not_yet_checked(self):
        self.assertEqual(mrr.badge_text(None), "Not yet checked")
        self.assertEqual(mrr.badge_html_for("not-in-the-summary", {}), mrr.badge_html(None))
        self.assertEqual(mrr.summary_row("absent", {}), None)
        self.assertIn(">Not yet checked</span>", mrr.badge_html_for("absent", {}))

    def test_insufficient_is_not_a_percentage_or_down(self):
        thin = _row("insufficient", ok_30d=2, n_30d=2, rate_30d=1.0)
        text = mrr.badge_text(thin)
        self.assertEqual(text, "Not yet checked")
        self.assertNotRegex(text, r"%|down")
        self.assertIsNone(mrr.rate_sample(thin))

    def test_a_rate_label_with_fewer_than_three_checks_is_not_a_sample(self):
        corrupt = _row("rate", ok_30d=2, n_30d=2, rate_30d=1.0)
        self.assertIsNone(mrr.rate_sample(corrupt))
        self.assertEqual(mrr.responds_attrs("corrupt", {"corrupt": corrupt}), ' data-resp="0"')


class RespondsSortTests(unittest.TestCase):
    def test_only_a_thick_rate_moves_and_a_thin_sample_does_not_jump(self):
        # Today's order is stars, then ratings, then recent push, then maturity.
        # The caller passes that order. Responds does not recompute it.
        today = [
            {"slug": "famous", "github_stars": 50000},
            {"slug": "thin", "github_stars": 40000},
            {"slug": "mid", "github_stars": 1000},
            {"slug": "best", "github_stars": 100},
            {"slug": "auth", "github_stars": 50},
            {"slug": "local", "github_stars": 10},
        ]
        servers = {
            "thin": {"display": "insufficient", "ok_30d": 2, "n_30d": 2, "rate_30d": 1.0},
            "mid": {"display": "rate", "ok_30d": 2, "n_30d": 4, "rate_30d": 0.5},
            "best": {"display": "rate", "ok_30d": 6, "n_30d": 6, "rate_30d": 1.0},
            "auth": {"display": "needs_auth", "auth_30d": 4, "ok_30d": 0, "n_30d": 0, "rate_30d": None},
            "local": {"display": "local_only"},
        }
        ordered = [x["slug"] for x in mrr.responds_sort(today, servers)]
        self.assertEqual(ordered, ["best", "mid", "famous", "thin", "auth", "local"])
        # 2/2 must not leap famous, and must not leap the measured servers as a fake 100%.
        self.assertLess(ordered.index("famous"), ordered.index("thin"))
        self.assertLess(ordered.index("best"), ordered.index("thin"))

    def test_same_rate_uses_n_30d_then_todays_order(self):
        today = [{"slug": "a"}, {"slug": "b"}, {"slug": "c"}, {"slug": "plain"}]
        servers = {
            "a": {"display": "rate", "ok_30d": 3, "n_30d": 6, "rate_30d": 0.5},
            "b": {"display": "rate", "ok_30d": 5, "n_30d": 10, "rate_30d": 0.5},
            "c": {"display": "rate", "ok_30d": 5, "n_30d": 10, "rate_30d": 0.5},
        }
        ordered = [x["slug"] for x in mrr.responds_sort(today, servers)]
        self.assertEqual(ordered, ["b", "c", "a", "plain"])

    def test_empty_summary_keeps_todays_order(self):
        today = [{"slug": "b"}, {"slug": "a"}]
        self.assertEqual(mrr.responds_sort(today, {}), today)

    def test_task_rank_then_responds_keeps_the_thin_server_behind_stars(self):
        import atexit
        import build_extras
        import build_mcp_tasks

        atexit.unregister(build_extras._apply_featured)
        items = [
            {"slug": "thin-high", "name": "Thin High", "github_stars": 9000, "maturity": "Active"},
            {"slug": "measured", "name": "Measured", "github_stars": 20, "maturity": "Active"},
            {"slug": "quiet", "name": "Quiet", "github_stars": 100, "maturity": "Active"},
        ]
        today = build_mcp_tasks.rank(items)
        self.assertEqual([x["slug"] for x in today], ["thin-high", "quiet", "measured"])
        servers = {
            "thin-high": {"display": "insufficient", "ok_30d": 2, "n_30d": 2, "rate_30d": 1.0},
            "measured": {"display": "rate", "ok_30d": 3, "n_30d": 3, "rate_30d": 1.0},
        }
        ordered = [x["slug"] for x in mrr.responds_sort(today, servers)]
        self.assertEqual(ordered, ["measured", "thin-high", "quiet"])
        self.assertLess(ordered.index("thin-high"), ordered.index("quiet"))


class PageTests(unittest.TestCase):
    def test_tool_stamp_uses_the_badge_and_skips_other_categories(self):
        html = '<div class="badges"><span class="b cat">MCP servers</span><span class="b">Open source</span></div>\n<h1 class="icoh"><span>X</span></h1>'
        out = build_rich.stamp_tool_badge(html, {"slug": "missing-server", "category": "MCP servers"})
        self.assertIn('<span class="b" data-mcp-health="1">Not yet checked</span>', out)
        self.assertEqual(build_rich.stamp_tool_badge(out, {"slug": "missing-server", "category": "MCP servers"}), out)
        plain = build_rich.stamp_tool_badge(html, {"slug": "cursor", "category": "coding"})
        self.assertEqual(plain, html)

    def test_sample_pages_render_the_badge_and_the_responds_sort(self):
        tool = (ROOT / "tools" / "github-mcp-server.html").read_text(encoding="utf-8")
        self.assertIn('<span class="b" data-mcp-health="1">Not yet checked</span>', tool)
        self.assertNotRegex(BADGE.search(tool).group(1), r"%|down")

        cat = (ROOT / "categories" / "mcp-servers.html").read_text(encoding="utf-8")
        self.assertIn('<span class="b" data-mcp-health="1">Not yet checked</span>', cat)
        self.assertIn('<option value="responds">Responds</option>', cat)
        # Counts move with every catalog build, so read them from the published count file.
        total = json.loads((ROOT / "data" / "site_counts.json").read_text(encoding="utf-8"))["mcp_servers"]
        self.assertIn(f"{total:,} MCP servers", cat)
        live = re.search(r"([\d,]+) of ([\d,]+) checked servers live", cat)
        self.assertIsNotNone(live)
        self.assertEqual(live.group(2), f"{total:,}")
        self.assertLessEqual(int(live.group(1).replace(",", "")), total)
        self.assertNotIn("responded today", cat[:8000])

        best = (ROOT / "best" / "open-source-mcp-servers.html").read_text(encoding="utf-8")
        self.assertIn('<span class="b" data-mcp-health="1">Not yet checked</span>', best)
        self.assertIn('data-responds-sort', best)
        self.assertIn('<option value="responds">Responds</option>', best)
        self.assertIn("data-responds-list", best)
        self.assertIn('src="../mcp-responds.js?v=', best)

        client = (ROOT / "best" / "mcp-servers-for-claude-code.html").read_text(encoding="utf-8")
        self.assertIn('data-mcp-health="1">Not yet checked</span>', client)
        self.assertIn("data-responds-list", client)

        task = (ROOT / "mcp" / "database-mcp-servers.html").read_text(encoding="utf-8")
        self.assertIn('data-mcp-health="1">Not yet checked</span>', task)
        self.assertIn("data-responds-list", task)
        self.assertIn("GitHub stars recorded on each listing", task)

        home = (ROOT / "index.html").read_text(encoding="utf-8")
        tools = json.loads((ROOT / "data" / "site_counts.json").read_text(encoding="utf-8"))["tools"]
        self.assertIn(f"{tools:,}", home)
        self.assertIn(f"{total:,}", home)

    def test_deferred_category_cards_carry_the_same_badge(self):
        data = json.loads((ROOT / "categories" / "mcp-servers.more.json").read_text(encoding="utf-8"))
        blob = data["g0"]
        self.assertGreater(blob.count('data-mcp-health="1">Not yet checked</span>'), 1000)
        self.assertIn('data-resp="0"', blob)
        self.assertNotIn('data-resp="1"', blob)

    def test_sort_script_ignores_anything_that_is_not_a_thick_rate(self):
        js = (ROOT / "mcp-responds.js").read_text(encoding="utf-8")
        cat = (ROOT / "catfilter.js").read_text(encoding="utf-8")
        for src in (js, cat):
            self.assertIn('dataset.resp==="1"', src)
            self.assertIn("dataset.rr", src)
            self.assertIn("dataset.rn", src)
        self.assertIn("responds_sort", js)


if __name__ == "__main__":
    unittest.main()
