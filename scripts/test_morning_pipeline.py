#!/usr/bin/env python3
"""The morning pipeline retries recheck once and does not push after a second failure."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import morning_pipeline


class MorningPipelineTest(unittest.TestCase):
    def test_a_passing_recheck_pushes_without_waiting(self):
        calls = []
        pushed = []

        def recheck():
            calls.append("recheck")
            return 0

        def push():
            pushed.append("push")
            return 0

        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "discovery-note.txt"
            code = morning_pipeline.run(
                recheck=recheck, push=push, sleep=lambda _s: calls.append("sleep"), note=note, wait=300
            )
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["recheck"])
        self.assertEqual(pushed, ["push"])
        self.assertFalse(note.exists())

    def test_one_failure_retries_after_300s_then_pushes(self):
        results = iter([1, 0])
        waits = []

        def recheck():
            return next(results)

        pushed = []
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "discovery-note.txt"
            code = morning_pipeline.run(
                recheck=recheck,
                push=lambda: pushed.append("push") or 0,
                sleep=waits.append,
                note=note,
                wait=300,
            )
            text = note.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(waits, [300])
        self.assertEqual(pushed, ["push"])
        self.assertTrue(text.startswith("RETRY "))
        self.assertIn("recheck failed; retrying once after 300s", text)

    def test_a_second_failure_stops_before_push(self):
        waits = []
        pushed = []
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "discovery-note.txt"
            code = morning_pipeline.run(
                recheck=lambda: 1,
                push=lambda: pushed.append("push") or 0,
                sleep=waits.append,
                note=note,
                wait=300,
            )
            lines = note.read_text(encoding="utf-8").splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(waits, [300])
        self.assertEqual(pushed, [])
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("RETRY "))

    def test_retry_line_uses_the_given_clock(self):
        when = datetime(2026, 11, 19, 17, 0, tzinfo=timezone.utc)
        self.assertEqual(
            morning_pipeline.retry_line(when),
            "RETRY 2026-11-19T09:00:00-08:00 recheck failed; retrying once after 300s",
        )


if __name__ == "__main__":
    unittest.main()
