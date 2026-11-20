#!/usr/bin/env python3
"""The morning pipeline stops at the first failing check.

The live audit is the only step that waits 300 seconds and runs again.
A network error from that fetch is a failure, so the retry actually runs.
"""
from __future__ import annotations

import io
import tempfile
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import morning_pipeline


class MorningPipelineTest(unittest.TestCase):
    def _run(self, runners, steps=None, **kwargs):
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            note = root / "discovery-note.txt"
            with redirect_stdout(buf):
                code = morning_pipeline.run(
                    root=root,
                    steps=steps,
                    runners=runners,
                    note=note,
                    wait=300,
                    **kwargs,
                )
            report = next(root.glob("reports/pipeline-failure-*.md"), None)
            note_text = note.read_text(encoding="utf-8") if note.exists() else ""
            report_text = report.read_text(encoding="utf-8") if report else ""
        return code, buf.getvalue().splitlines(), note_text, report_text

    def test_passing_steps_push_without_waiting(self):
        calls = []
        pushed = []
        steps = [morning_pipeline.Step("recheck"), morning_pipeline.Step("tests")]

        def recheck():
            calls.append("recheck")
            return 0

        def tests():
            calls.append("tests")
            return 0

        code, lines, note, report = self._run(
            {"recheck": recheck, "tests": tests},
            steps=steps,
            push=lambda: pushed.append("push") or 0,
            sleep=lambda _s: calls.append("sleep"),
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["recheck", "tests"])
        self.assertEqual(pushed, ["push"])
        self.assertEqual(note, "")
        self.assertEqual(report, "")
        self.assertFalse(any(line.startswith("PIPELINE FAILED:") for line in lines))

    def test_a_recheck_failure_stops_without_retry_or_later_steps(self):
        calls = []
        when = datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)
        code, lines, note, report = self._run(
            {
                "recheck": lambda: 1,
                "predeploy": lambda: calls.append("predeploy") or 0,
            },
            steps=[morning_pipeline.Step("recheck"), morning_pipeline.Step("predeploy")],
            push=lambda: calls.append("push") or 0,
            sleep=lambda seconds: calls.append(seconds),
            now=lambda: when,
        )
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertEqual(note, "")
        self.assertIn("Step: recheck", report)
        self.assertIn("2026-11-20", report)
        self.assertEqual(lines[-1], "PIPELINE FAILED: recheck: exit 1")
        self.assertEqual(sum(1 for line in report.splitlines() if line.startswith("Step:")), 1)

    def test_a_network_failure_retries_once_after_300s(self):
        attempts = {"n": 0}
        waits = []
        pushed = []
        later = []

        def live():
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise urllib.error.URLError("timed out")
            return 0

        code, lines, note, report = self._run(
            {"live": live, "tests": lambda: later.append("tests") or 0},
            steps=[morning_pipeline.Step("live", transient=True), morning_pipeline.Step("tests")],
            push=lambda: pushed.append("push") or 0,
            sleep=waits.append,
            now=lambda: datetime(2026, 11, 19, 17, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(code, 0)
        self.assertEqual(attempts["n"], 2)
        self.assertEqual(waits, [300])
        self.assertEqual(later, ["tests"])
        self.assertEqual(pushed, ["push"])
        self.assertEqual(report, "")
        self.assertTrue(note.startswith("RETRY "))
        self.assertIn("live failed; retrying once after 300s", note)
        self.assertTrue(any("URLError" in line for line in lines))

    def test_a_second_network_failure_writes_one_summary_and_does_not_push(self):
        calls = []
        code, lines, note, report = self._run(
            {
                "live": lambda: (_ for _ in ()).throw(urllib.error.URLError("timed out")),
                "tests": lambda: calls.append("tests") or 0,
            },
            steps=[morning_pipeline.Step("live", transient=True), morning_pipeline.Step("tests")],
            push=lambda: calls.append("push") or 0,
            sleep=calls.append,
        )
        self.assertEqual(code, 1)
        self.assertEqual(calls, [300])
        self.assertIn("Step: live", report)
        self.assertIn("URLError", report)
        self.assertEqual(len(note.splitlines()), 1)
        self.assertTrue(lines[-1].startswith("PIPELINE FAILED: live:"))

    def test_retry_line_uses_the_given_clock(self):
        when = datetime(2026, 11, 19, 17, 0, tzinfo=timezone.utc)
        self.assertEqual(
            morning_pipeline.retry_line(when, "live"),
            "RETRY 2026-11-19T09:00:00-08:00 live failed; retrying once after 300s",
        )

    def test_skip_live_still_pushes_when_local_checks_pass(self):
        calls = []
        code, _lines, _note, _report = self._run(
            {"recheck": lambda: 0, "live": lambda: calls.append("live") or 1},
            steps=[morning_pipeline.Step("recheck"), morning_pipeline.Step("live", transient=True)],
            push=lambda: calls.append("push") or 0,
            sleep=lambda _s: calls.append("sleep"),
            skip={"live"},
        )
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["push"])

    def test_default_steps_retry_only_the_live_audit(self):
        steps = morning_pipeline.pipeline_steps()
        self.assertEqual([step.name for step in steps], ["recheck", "predeploy", "audit", "tests", "live"])
        self.assertEqual([step.name for step in steps if step.transient], ["live"])
        root = morning_pipeline.ROOT
        self.assertEqual(morning_pipeline.command_for("recheck", root)[0][-1], str(root / "scripts" / "recheck.py"))
        self.assertIn("--predeploy", morning_pipeline.command_for("predeploy", root)[0])
        self.assertNotIn("--predeploy", morning_pipeline.command_for("audit", root)[0])
        self.assertNotIn("--live", morning_pipeline.command_for("audit", root)[0])
        self.assertIn("--live", morning_pipeline.command_for("live", root)[0])
        tests = morning_pipeline.command_for("tests", root)
        self.assertIn("test_publish_gate.py", tests[2][-1])
        self.assertIn("test_morning_audit.py", tests[3][-1])

    def test_live_http_network_error_is_a_failed_response(self):
        import morning_audit

        def boom(*_args, **_kwargs):
            raise urllib.error.URLError("timed out")

        original = urllib.request.urlopen
        urllib.request.urlopen = boom
        try:
            status, _headers, body = morning_audit._http("https://agentscouthq.com/")
        finally:
            urllib.request.urlopen = original
        self.assertEqual(status, 0)
        self.assertIn("network error", body)


if __name__ == "__main__":
    unittest.main()
