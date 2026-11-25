#!/usr/bin/env python3
"""The daily handshake publish path: restamp, fresh main, one open pull request."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "guardrails"))

import mcp_health_pages as pages_job  # noqa: E402
import mcp_health_publish as publish  # noqa: E402
import mcp_response_rate as mrr  # noqa: E402


SERVERS = {
    "one": {
        "disposition": "remote",
        "display": "rate",
        "ok_30d": 3,
        "n_30d": 3,
        "rate_30d": 1,
        "probes": 3,
    }
}


class RestampTests(unittest.TestCase):
    def test_badge_responds_and_handshake_follow_the_summary(self):
        text = (
            '<link rel="canonical" href="https://agentscouthq.com/tools/one.html">'
            '<span class="b" data-mcp-health="1">Not yet checked</span>'
            '<a class="card tile" data-s="one" data-resp="0" href="../tools/one.html"></a>'
            "<p>Handshake check: 1 of 2 remote servers checked so far. "
            "This is the initialize + tools/list probe, updated daily around 7:15 AM Pacific, "
            "separate from the link check around 7 AM PT.</p>"
        )
        updated, missed = pages_job.rewrite_document(
            text,
            servers=SERVERS,
            default_slug="one",
            sentence="Handshake check: 2 of 2 remote servers checked.",
            home_html="",
            check_html=None,
        )
        self.assertEqual(missed, [])
        self.assertIn(mrr.badge_html_for("one", SERVERS), updated)
        self.assertIn(mrr.responds_attrs("one", SERVERS), updated)
        self.assertIn("Handshake check: 2 of 2 remote servers checked.", updated)
        self.assertNotIn("Not yet checked", updated)
        self.assertNotIn('data-resp="0"', updated)

    def test_escaped_json_cards_keep_their_quotes(self):
        raw = (
            r'<a class=\"card tile\" data-s=\"one\" data-resp=\"0\" href=\"../tools/one.html\">'
            r'<span class=\"b\" data-mcp-health=\"1\">Not yet checked</span></a>'
        )
        updated, missed = pages_job.rewrite_document(raw, servers=SERVERS, default_slug=None)
        self.assertEqual(missed, [])
        self.assertIn(r'data-resp=\"1\"', updated)
        self.assertIn(r'data-rr=\"1.000\"', updated)
        self.assertIn("Responded 3/3 checks in last 30 days", updated)
        self.assertNotIn('data-resp="1"', updated)

    def test_new_sitemap_url_is_reported(self):
        before = "<urlset><url><loc>https://agentscouthq.com/tools/one.html</loc></url></urlset>"
        after = before.replace(
            "</urlset>",
            "<url><loc>https://agentscouthq.com/tools/two.html</loc></url></urlset>",
        )
        added = pages_job.new_sitemap_urls(ROOT, before, after)
        self.assertEqual(added, ["https://agentscouthq.com/tools/two.html"])
        self.assertEqual(pages_job.new_sitemap_urls(ROOT, before, before), [])


class PublishRuleTests(unittest.TestCase):
    def test_union_keeps_main_order_and_appends_new_rows(self):
        base = '{"slug":"a"}\n{"slug":"b"}\n'
        extra = '{"slug":"b"}\n{"slug":"c"}\n'
        self.assertEqual(publish.union_jsonl(base, extra), '{"slug":"a"}\n{"slug":"b"}\n{"slug":"c"}\n')

    def test_health_without_html_is_refused(self):
        message = publish.commit_block(["data/mcp-health/summary.json", "data/mcp-health/state.json"])
        self.assertIn("source/builder files changed", message)
        self.assertIn("data/mcp-health/summary.json", message)
        self.assertIn("no published *.html", message)

    def test_health_plus_rebuilt_html_is_allowed(self):
        paths = [
            "data/mcp-health/2026-11.jsonl",
            "data/mcp-health/summary.json",
            "data/mcp-health/state.json",
            "tools/one.html",
            "categories/mcp-servers.more.json",
            "tasks/connecting-tools-mcp.more.json",
            "tasks/writing-code.more.json",
            "llms.txt",
        ]
        self.assertIsNone(publish.commit_block(paths))
        for path in (
            "tasks/connecting-tools-mcp.more.json",
            "tasks/writing-code.more.json",
            "categories/mcp-servers.more.json",
        ):
            self.assertTrue(publish.allowed_path(path))

    def test_allow_list_stays_tight_around_task_fragments(self):
        self.assertFalse(publish.allowed_path("tasks/nested/writing-code.more.json"))
        self.assertFalse(publish.allowed_path("tasks/writing-code.json"))
        self.assertFalse(publish.allowed_path("best/mcp.more.json"))
        self.assertFalse(publish.allowed_path("categories/nested/mcp-servers.more.json"))

    def test_only_a_new_month_log_may_be_untracked(self):
        rows = [
            ("??", "data/mcp-health/2026-12.jsonl"),
            (" M", "data/mcp-health/summary.json"),
            (" M", "tools/one.html"),
            (" M", "tasks/connecting-tools-mcp.more.json"),
        ]
        self.assertTrue(publish.is_new_month_log("??", "data/mcp-health/2026-12.jsonl"))
        self.assertIsNone(publish.review_status(rows))
        self.assertFalse(publish.is_new_month_log("??", "data/mcp-health/2026-13.jsonl"))
        self.assertFalse(publish.is_new_month_log("??", "data/mcp-health/notes.txt"))
        self.assertFalse(publish.is_new_month_log("A ", "data/mcp-health/2026-12.jsonl"))
        refused = publish.review_status([("??", "tools/extra.html"), (" M", "tools/one.html")])
        self.assertIn("tools/extra.html", refused)
        self.assertIn("status other than a modification", refused)

    def test_sitemap_and_new_paths_are_refused(self):
        message = publish.commit_block(["data/mcp-health/summary.json", "tools/one.html", "sitemap.xml"])
        self.assertIn("unexpected paths", message)
        self.assertIn("sitemap.xml", message)

    def test_branch_name_stays_on_the_bot_prefix(self):
        self.assertEqual(publish.make_branch("2026-11-25", "455"), "bot/mcp-health-2026-11-25-455")
        with self.assertRaises(RuntimeError):
            publish.make_branch("2026-11-25", "main")
        with self.assertRaises(RuntimeError):
            publish.make_branch("2026-11-25", "../main")

    def test_older_bot_pull_requests_sort_oldest_first(self):
        rows = publish.select_health_prs(
            [
                {"number": 2, "headRefName": "bot/mcp-health-2026-11-24-9", "updatedAt": "2026-11-24T00:00:00Z"},
                {"number": 1, "headRefName": "feature", "updatedAt": "2026-11-25T00:00:00Z"},
                {"number": 3, "headRefName": "bot/mcp-health-2026-11-23-8", "updatedAt": "2026-11-23T00:00:00Z"},
                {
                    "number": 9,
                    "headRefName": "bot/mcp-health-2026-11-22-1",
                    "updatedAt": "2026-11-22T00:00:00Z",
                    "isCrossRepository": True,
                },
            ]
        )
        self.assertEqual([row["number"] for row in rows], [3, 2])

    def test_carried_state_is_kept_only_when_rows_are_new(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        health = tmp / "data" / "mcp-health"
        health.mkdir(parents=True)
        (health / "2026-11.jsonl").write_text('{"slug":"a"}\n', encoding="utf-8")
        (health / "state.json").write_text('{"next_slug":"main"}\n', encoding="utf-8")
        already = {"2026-11.jsonl": '{"slug":"a"}\n', "state.json": '{"next_slug":"old"}\n'}
        self.assertFalse(publish.overlay_carried(tmp, already))
        self.assertEqual(json.loads((health / "state.json").read_text(encoding="utf-8"))["next_slug"], "main")
        fresh = {"2026-11.jsonl": '{"slug":"b"}\n', "state.json": '{"next_slug":"next"}\n'}
        self.assertTrue(publish.overlay_carried(tmp, fresh))
        self.assertIn('"slug":"b"', (health / "2026-11.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((health / "state.json").read_text(encoding="utf-8"))["next_slug"], "next")

    def test_merge_keeps_probe_state_and_main_rows(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        health = tmp / "data" / "mcp-health"
        health.mkdir(parents=True)
        (health / "2026-11.jsonl").write_text('{"slug":"main-only","ts":"2026-11-25T00:00:00Z"}\n', encoding="utf-8")
        probe_summary = {
            "generated": "2026-11-25T01:00:00-08:00",
            "min_probes": 3,
            "registry_complete": False,
            "servers": {
                "probed": {"disposition": "remote", "display": "insufficient", "probes": 1},
            },
        }
        probe = {
            "2026-11.jsonl": '{"slug":"probed","ts":"2026-11-25T01:00:00Z","outcome":"responded"}\n',
            "state.json": '{"deferred":["later"],"next_slug":"probed","updated":"2026-11-25T01:00:00-08:00"}\n',
            "summary.json": json.dumps(probe_summary),
        }
        publish.merge_probe_health(tmp, probe)
        lines = (health / "2026-11.jsonl").read_text(encoding="utf-8")
        self.assertIn('"slug":"main-only"', lines)
        self.assertIn('"slug":"probed"', lines)
        state = json.loads((health / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["next_slug"], "probed")
        self.assertEqual(state["deferred"], ["later"])
        summary = json.loads((health / "summary.json").read_text(encoding="utf-8"))
        self.assertIn("probed", summary["servers"])
        self.assertIn("main-only", summary["servers"])


class RebuildFixtureTests(unittest.TestCase):
    def test_fixture_restamp_does_not_add_a_sitemap_url(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        health = tmp / "data" / "mcp-health"
        health.mkdir(parents=True)
        (health / "summary.json").write_text(
            json.dumps({"servers": SERVERS}) + "\n",
            encoding="utf-8",
        )
        (health / "2026-11.jsonl").write_text(
            '{"slug":"one","ts":"2026-11-25T00:00:00Z","outcome":"responded","transport":"streamable-http",'
            '"latency_ms":10,"protocol_version":"2025-06-18","tool_count":1}\n',
            encoding="utf-8",
        )
        page = tmp / "tools" / "one.html"
        page.parent.mkdir()
        page.write_text(
            '<link rel="canonical" href="https://agentscouthq.com/tools/one.html">'
            '<span class="b" data-mcp-health="1">Not yet checked</span>'
            '<section id="reviews"></section>',
            encoding="utf-8",
        )
        sitemap = "<urlset><url><loc>https://agentscouthq.com/tools/one.html</loc></url></urlset>\n"
        (tmp / "sitemap.xml").write_text(sitemap, encoding="utf-8")
        report = pages_job.rebuild_pages(tmp)
        self.assertGreaterEqual(report["files"], 1)
        self.assertEqual(report["sitemap_urls_added"], 0)
        self.assertEqual((tmp / "sitemap.xml").read_text(encoding="utf-8"), sitemap)
        rebuilt = page.read_text(encoding="utf-8")
        self.assertIn("Responded 3/3 checks in last 30 days", rebuilt)
        self.assertIn('data-mcp-check="1"', rebuilt)
        self.assertNotIn("tools/two.html", rebuilt)

    def test_replacement_text_is_not_read_as_a_backreference(self):
        cadence = pages_job.CADENCE_FALLBACK
        text = "Handshake check: 1 of 2 remote servers checked so far. " + cadence
        updated, missed = pages_job.rewrite_document(
            text,
            servers=SERVERS,
            sentence=r"Handshake check: \1 stayed literal.",
            cadence=cadence,
        )
        self.assertEqual(missed, [])
        self.assertIn(r"\1 stayed literal.", updated)


class CheckWaitTests(unittest.TestCase):
    def _run(self, rows_for):
        def run(argv, **_kwargs):
            workflow = argv[argv.index("--workflow") + 1]

            class Result:
                returncode = 0
                stdout = json.dumps(rows_for(workflow))
                stderr = ""

            return Result()

        return run

    def test_auto_merge_waits_until_all_four_succeed(self):
        calls = {"n": 0}

        def rows_for(_workflow):
            calls["n"] += 1
            return [{
                "headSha": "abc",
                "status": "completed",
                "conclusion": "success",
                "createdAt": "2026-11-25T00:00:00Z",
            }]

        failed = publish.wait_for_checks(
            "owner/repo", "bot/mcp-health-2026-11-25-1", "abc",
            run=self._run(rows_for), sleep=lambda _seconds: None, clock=lambda: 0, timeout=30, poll=15,
        )
        self.assertEqual(failed, [])
        self.assertEqual(calls["n"], len(publish.CI_WORKFLOWS))

    def test_a_failed_check_blocks_auto_merge(self):
        def rows_for(workflow):
            conclusion = "failure" if workflow == "gitleaks.yml" else "success"
            return [{
                "headSha": "abc",
                "status": "completed",
                "conclusion": conclusion,
                "createdAt": "2026-11-25T00:00:00Z",
            }]

        failed = publish.wait_for_checks(
            "owner/repo", "branch", "abc",
            run=self._run(rows_for), sleep=lambda _seconds: (_ for _ in ()).throw(AssertionError("should not poll again")),
            clock=lambda: 0, timeout=30, poll=15,
        )
        self.assertEqual(failed, ["gitleaks.yml failure"])

    def test_timeout_leaves_the_unfinished_workflows(self):
        now = {"t": 0}

        def clock():
            return now["t"]

        def sleep(seconds):
            now["t"] += seconds

        def rows_for(workflow):
            if workflow == "guardrails.yml":
                return [{
                    "headSha": "abc",
                    "status": "completed",
                    "conclusion": "success",
                    "createdAt": "2026-11-25T00:00:00Z",
                }]
            return [{
                "headSha": "abc",
                "status": "in_progress",
                "conclusion": None,
                "createdAt": "2026-11-25T00:00:00Z",
            }]

        failed = publish.wait_for_checks(
            "owner/repo", "branch", "abc",
            run=self._run(rows_for), sleep=sleep, clock=clock, timeout=30, poll=15,
        )
        self.assertIn("security.yml", failed)
        self.assertIn("gitleaks.yml", failed)
        self.assertIn("codeql.yml", failed)
        self.assertNotIn("guardrails.yml", failed)


if __name__ == "__main__":
    unittest.main()
